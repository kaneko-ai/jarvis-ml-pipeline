(function (global) {
    function normalizeError(err, response) {
        if (err && err.kind) {
            return err;
        }

        const status = response && response.status ? response.status : 0;
        let kind = 'SERVER_ERROR';
        let message = 'Unexpected error';
        let detail = '';
        let hint = '';

        if (err && err.name === 'AbortError') {
            kind = 'TIMEOUT';
            message = 'Request timed out';
            hint = 'ネットワーク状況を確認してください。';
        } else if (!response && err instanceof TypeError) {
            kind = 'NO_CONNECTION';
            message = 'Network request failed';
            hint = 'APIサーバに接続できません。';
        } else if (err instanceof SyntaxError) {
            kind = 'BAD_RESPONSE';
            message = 'Failed to parse response';
            hint = 'サーバのレスポンス形式が不正です。';
        } else if (status === 401 || status === 403) {
            kind = 'UNAUTHORIZED';
            message = 'Unauthorized';
            hint = 'Settingsでトークンを設定してください。';
        } else if (status === 404 || status === 501) {
            kind = 'NOT_IMPLEMENTED';
            message = 'Endpoint not implemented';
            hint = '代替の成果物ファイルを確認してください。';
        } else if (status >= 500) {
            kind = 'SERVER_ERROR';
            message = 'Server error';
            hint = 'サーバの状態を確認してください。';
        } else if (status > 0 && status < 500) {
            kind = 'BAD_RESPONSE';
            message = 'Bad response';
        } else if (!response && err) {
            kind = 'NO_CONNECTION';
            message = 'Network error';
        }

        if (err && err.message) {
            detail = err.message;
        }

        return {
            kind,
            status,
            message,
            detail,
            hint
        };
    }

    global.JarvisErrors = {
        normalizeError
    };
})(window);
