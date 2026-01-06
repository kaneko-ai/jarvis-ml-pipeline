---
name: mcp
description: MCPサーバの高品質設計。ワークフローツール＋発見しやすい命名＋構造化出力
---

# MCP

## 設計
- API網羅と作業単位ツールの両立
- 命名: prefix_action（github_create_issue 等）
- エラーは解決指向

## 実装
- 言語: TypeScript推奨
- 入力: Zod、出力: structuredContent
- 注釈: readOnlyHint/destructiveHint等

## 検証
- npm run build / MCP Inspector

## 評価
- 独立・複合・検証可能な10問

## 参照
- [SPEC](SPEC.md)
- [REVIEW](REVIEW.md)
- [TOKEN](TOKEN.md)
