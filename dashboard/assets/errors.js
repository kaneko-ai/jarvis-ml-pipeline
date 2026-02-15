(function (global) {
    const NOT_IMPLEMENTED_MESSAGE = "未実装：バックエンドAPIが存在しません";

    function normalizeNotImplemented(detail = "") {
        return {
            kind: "NOT_IMPLEMENTED",
            status: 501,
            message: NOT_IMPLEMENTED_MESSAGE,
            detail,
            hint: "personal core 対象外です",
        };
    }

    function normalizeError(err, response) {
        if (err && err.kind === "NOT_IMPLEMENTED") {
            return normalizeNotImplemented(err.detail || "");
        }
        if (err && err.kind) {
            return err;
        }

        const status = response && response.status ? response.status : 0;
        let kind = "SERVER_ERROR";
        let message = "Unexpected error";
        let detail = "";
        let hint = "";

        if (err && err.name === "AbortError") {
            kind = "TIMEOUT";
            message = "Request timed out";
            hint = "ネットワーク状態を確認してください。";
        } else if (!response && err instanceof TypeError) {
            kind = "NO_CONNECTION";
            message = "Network request failed";
            hint = "APIサーバーに接続できません。";
        } else if (err instanceof SyntaxError) {
            kind = "BAD_RESPONSE";
            message = "Failed to parse response";
            hint = "サーバーレスポンス形式が不正です。";
        } else if (status === 401 || status === 403) {
            kind = "UNAUTHORIZED";
            message = "Unauthorized";
            hint = "Settingsでトークンを設定してください。";
        } else if (status === 404 || status === 501) {
            return normalizeNotImplemented(err?.message || "");
        } else if (status >= 500) {
            kind = "SERVER_ERROR";
            message = "Server error";
            hint = "サーバー状態を確認してください。";
        } else if (status > 0 && status < 500) {
            kind = "BAD_RESPONSE";
            message = "Bad response";
        } else if (!response && err) {
            kind = "NO_CONNECTION";
            message = "Network error";
        }

        if (err && err.message) {
            detail = err.message;
        }

        return {
            kind,
            status,
            message,
            detail,
            hint,
        };
    }

    global.JarvisErrors = {
        normalizeError,
        normalizeNotImplemented,
    };
})(window);
