"""Drive resumable upload client for ops_extract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests


class DriveUploadError(RuntimeError):
    """Raised when resumable upload fails."""


class DriveResumableClient:
    def __init__(
        self,
        *,
        access_token: str,
        api_base_url: str | None = None,
        upload_base_url: str | None = None,
        timeout_sec: float = 30.0,
    ) -> None:
        self.access_token = access_token
        self.api_base_url = (api_base_url or "https://www.googleapis.com/drive/v3").rstrip("/")
        self.upload_base_url = (
            upload_base_url or "https://www.googleapis.com/upload/drive/v3/files"
        ).rstrip("/")
        self.timeout_sec = float(timeout_sec)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
        }

    def _is_google_mode(self) -> bool:
        return "googleapis.com" in self.upload_base_url

    def _request_json(
        self,
        *,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        json_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers={**self._headers(), "Content-Type": "application/json"},
            params=params,
            json=json_payload,
            timeout=self.timeout_sec,
        )
        if response.status_code >= 400:
            raise DriveUploadError(f"drive_api_failed:{response.status_code}:{response.text[:200]}")
        if not response.content:
            return {}
        payload = response.json()
        return payload if isinstance(payload, dict) else {}

    def start_session(
        self,
        *,
        filename: str,
        size: int,
        folder_id: str | None = None,
        mime_type: str = "application/octet-stream",
        resume_token: str | None = None,
    ) -> str:
        headers = self._headers()
        if self._is_google_mode():
            headers.update(
                {
                    "X-Upload-Content-Type": mime_type,
                    "X-Upload-Content-Length": str(size),
                    "Content-Type": "application/json; charset=UTF-8",
                }
            )
            metadata: dict[str, Any] = {"name": filename}
            if folder_id:
                metadata["parents"] = [folder_id]
            response = requests.post(
                f"{self.upload_base_url}?uploadType=resumable",
                headers=headers,
                data=json.dumps(metadata),
                timeout=self.timeout_sec,
            )
            if response.status_code >= 400:
                raise DriveUploadError(
                    f"start_session_failed:{response.status_code}:{response.text[:200]}"
                )
            session_uri = response.headers.get("Location", "").strip()
            if not session_uri:
                raise DriveUploadError("start_session_failed:missing_location")
            return session_uri

        response = requests.post(
            f"{self.upload_base_url}/resumable/start",
            headers={**headers, "Content-Type": "application/json"},
            json={
                "name": filename,
                "size": int(size),
                "folder_id": folder_id,
                "resume_token": resume_token or "",
                "mime_type": mime_type,
            },
            timeout=self.timeout_sec,
        )
        if response.status_code >= 400:
            raise DriveUploadError(
                f"start_session_failed:{response.status_code}:{response.text[:200]}"
            )
        data = response.json() if response.content else {}
        session_uri = str(data.get("session_uri", "")).strip() or response.headers.get(
            "Location", ""
        )
        if not session_uri:
            raise DriveUploadError("start_session_failed:missing_session_uri")
        return session_uri

    def upload_bytes(
        self,
        *,
        filename: str,
        raw: bytes,
        folder_id: str | None = None,
        chunk_bytes: int = 8 * 1024 * 1024,
        resume_token: str | None = None,
        session_uri: str | None = None,
    ) -> dict[str, Any]:
        size = len(raw)
        session = session_uri or self.start_session(
            filename=filename,
            size=size,
            folder_id=folder_id,
            resume_token=resume_token,
        )
        attempts = 0
        offset = 0
        file_id = ""
        last_response_payload: dict[str, Any] = {}

        while offset < size:
            end = min(size, offset + max(1, int(chunk_bytes)))
            chunk = raw[offset:end]
            headers = self._headers()
            headers.update(
                {
                    "Content-Length": str(len(chunk)),
                    "Content-Range": f"bytes {offset}-{end - 1}/{size}",
                }
            )
            resp = requests.put(session, headers=headers, data=chunk, timeout=self.timeout_sec)
            attempts += 1
            if resp.status_code in {200, 201}:
                data = resp.json() if resp.content else {}
                last_response_payload = data if isinstance(data, dict) else {}
                file_id = str(
                    last_response_payload.get("id") or last_response_payload.get("file_id") or ""
                )
                offset = end
                break
            if resp.status_code == 308:
                range_hdr = str(resp.headers.get("Range", "")).strip()
                if range_hdr.startswith("bytes=0-"):
                    try:
                        offset = int(range_hdr.split("-")[-1]) + 1
                    except Exception:
                        offset = end
                else:
                    offset = end
                continue
            raise DriveUploadError(f"upload_chunk_failed:{resp.status_code}:{resp.text[:200]}")

        if not file_id:
            if offset < size:
                raise DriveUploadError("upload_incomplete")
            file_id = last_response_payload.get("id") or last_response_payload.get("file_id") or ""
            file_id = str(file_id).strip() or f"session:{hash(session)}"

        return {
            "file_id": file_id,
            "session_uri": session,
            "attempts": attempts,
            "uploaded_bytes": size,
        }

    def upload_file(
        self,
        *,
        path: Path,
        folder_id: str | None = None,
        chunk_bytes: int = 8 * 1024 * 1024,
        resume_token: str | None = None,
        session_uri: str | None = None,
    ) -> dict[str, Any]:
        return self.upload_bytes(
            filename=path.name,
            raw=path.read_bytes(),
            folder_id=folder_id,
            chunk_bytes=chunk_bytes,
            resume_token=resume_token,
            session_uri=session_uri,
        )

    def get_file_metadata(
        self,
        file_id: str,
        *,
        fields: str = "id,name,size,md5Checksum,modifiedTime,version",
    ) -> dict[str, Any]:
        file_id = str(file_id).strip()
        if not file_id:
            raise DriveUploadError("metadata_failed:empty_file_id")
        if self._is_google_mode():
            return self._request_json(
                method="GET",
                url=f"{self.api_base_url}/files/{file_id}",
                params={"fields": fields, "supportsAllDrives": "true"},
            )
        return self._request_json(
            method="GET",
            url=f"{self.api_base_url}/files/{file_id}",
            params={"fields": fields},
        )

    def list_children(
        self,
        *,
        parent_id: str | None,
        q: str | None = None,
        fields: str = "files(id,name,mimeType)",
    ) -> list[dict[str, Any]]:
        if self._is_google_mode():
            clauses: list[str] = []
            if parent_id:
                clauses.append(f"'{parent_id}' in parents")
            if q:
                clauses.append(q)
            query = " and ".join(clauses)
            payload = self._request_json(
                method="GET",
                url=f"{self.api_base_url}/files",
                params={
                    "q": query,
                    "fields": fields,
                    "supportsAllDrives": "true",
                    "includeItemsFromAllDrives": "true",
                },
            )
            files = payload.get("files", [])
            return files if isinstance(files, list) else []
        payload = self._request_json(
            method="GET",
            url=f"{self.api_base_url}/children",
            params={"parent_id": parent_id or "", "q": q or "", "fields": fields},
        )
        files = payload.get("files", [])
        return files if isinstance(files, list) else []

    def ensure_folder(self, *, name: str, parent_id: str | None = None) -> str:
        name = str(name).strip()
        if not name:
            raise DriveUploadError("ensure_folder_failed:empty_name")
        if self._is_google_mode():
            q_name = name.replace("'", "\\'")
            query = (
                "mimeType='application/vnd.google-apps.folder' "
                f"and name='{q_name}' and trashed=false"
            )
            if parent_id:
                query += f" and '{parent_id}' in parents"
            existing = self.list_children(
                parent_id=parent_id,
                q=query,
                fields="files(id,name,mimeType,createdTime)",
            )
            if len(existing) > 1:
                duplicate_ids = [
                    str(item.get("id", "")).strip()
                    for item in existing
                    if str(item.get("id", "")).strip()
                ]
                raise DriveUploadError(
                    f"duplicate_folder_detected:{name}:ids={','.join(duplicate_ids)}"
                )
            if len(existing) == 1:
                return str(existing[0].get("id", ""))
            payload: dict[str, Any] = {
                "name": name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            if parent_id:
                payload["parents"] = [parent_id]
            created = self._request_json(
                method="POST",
                url=f"{self.api_base_url}/files",
                params={"fields": "id,name"},
                json_payload=payload,
            )
            folder_id = str(created.get("id", "")).strip()
            if not folder_id:
                raise DriveUploadError(f"ensure_folder_failed:missing_id:{name}")
            return folder_id
        payload = self._request_json(
            method="POST",
            url=f"{self.api_base_url}/folders/ensure",
            json_payload={"name": name, "parent_id": parent_id or ""},
        )
        folder_id = str(payload.get("folder_id") or payload.get("id") or "").strip()
        if not folder_id:
            raise DriveUploadError(f"ensure_folder_failed:missing_id:{name}")
        return folder_id

    def list_permissions(self, file_id: str) -> list[dict[str, Any]]:
        file_id = str(file_id).strip()
        if not file_id:
            raise DriveUploadError("permissions_failed:empty_file_id")
        if self._is_google_mode():
            payload = self._request_json(
                method="GET",
                url=f"{self.api_base_url}/files/{file_id}/permissions",
                params={"fields": "permissions(id,type,role,allowFileDiscovery)"},
            )
            perms = payload.get("permissions", [])
            return perms if isinstance(perms, list) else []
        payload = self._request_json(
            method="GET",
            url=f"{self.api_base_url}/permissions",
            params={"file_id": file_id},
        )
        perms = payload.get("permissions", [])
        return perms if isinstance(perms, list) else []
