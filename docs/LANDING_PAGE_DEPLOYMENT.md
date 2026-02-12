> Authority: GUIDE (Level 3, Non-binding)

# 🚀 JARVIS Research OS - デプロイメントガイド

## 📋 デプロイ前チェックリスト

### 1. **トラッキングID設定** (必須)
`index-final.html` の以下の部分を編集:

```html
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<!-- ↑ 実際のGA4測定IDに置き換え -->

<!-- Hotjar -->
hjid: YOUR_HOTJAR_ID, // ← 実際のIDに置き換え
```

**取得方法:**
- **GA4**: [Google Analytics](https://analytics.google.com/) > 管理 > データストリーム > 測定ID
- **Hotjar**: [Hotjar](https://www.hotjar.com/) > サイト設定 > Tracking Code > Site ID

---

### 2. **OGP画像作成** (推奨)
必須サイズ: **1200×630px**

#### 推奨コンテンツ:
```
┌─────────────────────────────────┐
│  JARVIS Research OS             │
│  AI-Powered Literature Review   │
│                                 │
│  [ダッシュボードのスクリーン    │
│   ショットまたはロゴ]           │
│                                 │
│  ⚡ Evidence Grading             │
│  🔗 Citation Analysis            │
│  ⚠️  Contradiction Detection     │
└─────────────────────────────────┘
```

**保存先:**
```
/docs/og-image.png  (GitHub Pages用)
/public/og-image.png (Next.js用)
```

**画像作成ツール:**
- [Canva OGP Template](https://www.canva.com/templates/social-media/open-graph/)
- Figma (デザインツール)
- Photoshop / GIMP

---

### 3. **Favicon生成** (推奨)
必要なサイズ: 16×16, 32×32, 180×180, 192×192, 512×512

**自動生成ツール:**
- [Favicon Generator](https://realfavicongenerator.net/)
- [Favicon.io](https://favicon.io/)

**配置場所:**
```
/docs/
  ├── favicon.ico
  ├── favicon-16x16.png
  ├── favicon-32x32.png
  ├── apple-touch-icon.png
  └── site.webmanifest
```

---

## 🌐 GitHub Pagesデプロイ

### ステップ1: ファイル配置
```bash
cd jarvis-ml-pipeline

# docsフォルダに配置(GitHub Pages推奨)
mkdir -p docs
cp /path/to/index-final.html docs/index.html
cp /path/to/styles.css docs/
cp /path/to/script.js docs/
cp /path/to/analytics.js docs/

# OGP画像とfaviconも配置
cp og-image.png docs/
cp favicon.ico docs/
```

### ステップ2: Git push
```bash
git add docs/
git commit -m "🚀 Deploy: New landing page with SEO & analytics"
git push origin main
```

### ステップ3: GitHub Pages有効化
1. GitHub repo → **Settings**
2. **Pages** セクション
3. Source: **Deploy from a branch**
4. Branch: **main** / Folder: **/docs**
5. **Save** → 数分待機

**確認URL:**
```
https://kaneko-ai.github.io/jarvis-ml-pipeline/
```

---

## ⚡ Vercelデプロイ (高速・推奨)

### オプションA: CLI経由
```bash
npm install -g vercel
cd jarvis-ml-pipeline
vercel --prod
```

### オプションB: GitHubアプリ連携
1. [Vercel](https://vercel.com/) にログイン
2. **New Project** → GitHub repo選択
3. Framework Preset: **Other**
4. Root Directory: `docs`
5. **Deploy** クリック

**自動デプロイ設定:**
- `main`ブランチへのpush → 自動本番デプロイ
- PRブランチ → プレビューURL自動生成

---

## 🔍 SEO検証ツール

デプロイ後、以下で確認:

### 1. **構造化データテスト**
[Google Rich Results Test](https://search.google.com/test/rich-results)
→ URLを入力 → すべてのJSON-LDが認識されるか確認

### 2. **OGPプレビュー**
- [Facebook Debugger](https://developers.facebook.com/tools/debug/)
- [Twitter Card Validator](https://cards-dev.twitter.com/validator)
- [LinkedIn Inspector](https://www.linkedin.com/post-inspector/)

### 3. **モバイルフレンドリー**
[Google Mobile-Friendly Test](https://search.google.com/test/mobile-friendly)

### 4. **PageSpeed Insights**
[PageSpeed Insights](https://pagespeed.web.dev/)
→ 目標: デスクトップ95+、モバイル90+

---

## 📊 アナリティクス確認

### Google Analytics 4
1. [GA4ダッシュボード](https://analytics.google.com/)
2. **リアルタイム** → ページビュー確認
3. **イベント** → カスタムイベント確認:
   - `cta_click`
   - `demo_interaction`
   - `scroll_depth`

### Hotjar
1. [Hotjar Dashboard](https://insights.hotjar.com/)
2. **Heatmaps** → クリック/スクロール分布確認
3. **Recordings** → ユーザー行動記録再生

---

## 🐛 トラブルシューティング

### アナリティクスが動作しない
```javascript
// ブラウザのコンソールで確認
window.gtag // → function であればOK
window.hj   // → function であればOK
```

**Cookie同意バナーが表示されない:**
→ `localStorage.getItem('cookieConsent')` をクリア

### OGP画像が表示されない
1. キャッシュクリア (Facebook Debugger経由)
2. 画像URLが正しいか確認
3. 画像が1200×630pxか確認
4. HTTPSでアクセス可能か確認

### パフォーマンスが低い
```html
<!-- 画像をWebPに変換 -->
<img src="hero.webp" alt="Hero">

<!-- フォント最適化 -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preload" as="style" href="...">
```

---

## 📈 継続的改善

### A/Bテストツール
- [Google Optimize](https://optimize.google.com/)
- [VWO](https://vwo.com/)
- [Optimizely](https://www.optimizely.com/)

### SEO監視ツール
- [Google Search Console](https://search.google.com/search-console)
- [Ahrefs](https://ahrefs.com/)
- [SEMrush](https://www.semrush.com/)

---

## ✅ 最終チェックリスト

- [ ] GA4測定ID設定済み
- [ ] Hotjar ID設定済み
- [ ] OGP画像作成・配置済み (1200×630px)
- [ ] Favicon生成・配置済み
- [ ] GitHub PagesまたはVercelにデプロイ済み
- [ ] Google Rich Results Testで構造化データ確認
- [ ] Facebook DebuggerでOGPプレビュー確認
- [ ] PageSpeed Insights スコア90+
- [ ] モバイル実機で表示確認
- [ ] Cookie同意バナー動作確認
- [ ] アナリティクスのリアルタイムデータ確認

---

## 📞 サポート

問題が発生した場合:
1. [GitHub Issues](https://github.com/kaneko-ai/jarvis-ml-pipeline/issues)
2. ブラウザのコンソールログを確認
3. Network タブでリソース読み込みエラーを確認

**成功を祈っています!** 🚀


## API-separated demo mode (2026-02-13)

1. Deploy backend API (`jarvis_web.app`) on a public URL.
2. Open landing page and set `API Base URL` in Demo section.
3. Click `Save` and `Test`.
4. Demo panels run with API data when connection is available.
5. If connection is unavailable, browser fallback logic remains active.

Details: `docs/LANDING_PAGE_API_INTEGRATION_2026-02-13.md`
