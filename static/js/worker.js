/**
 * worker.js
 * ─────────────────────────────────────────────────────────────────
 * Điều phối hàng đợi xử lý ảnh (concurrency / multi-thread queue).
 * Gọi runForFile / runForUrl từ api.js theo số luồng được cấu hình.
 * ─────────────────────────────────────────────────────────────────
 */

async function runAll() {
    const hasFiles = state.files.length > 0;
    const hasUrls = state.urls.length > 0;
    if ((!hasFiles && !hasUrls) || state.running) return;

    state.completed = 0;
    state.failed = 0;
    setRunning(true);

    const concurrency = parseInt(threadsInput.value) || 1;
    const customVocab = customVocabInput.value.trim();

    // Tạo hàng đợi task
    const queue = [];
    state.files.forEach((obj, i) => queue.push({ type: "file", obj, index: i }));
    state.urls.forEach((obj, i) => queue.push({ type: "url", obj, index: i }));

    // Worker tiêu thụ hàng đợi
    async function worker() {
        while (queue.length > 0 && state.running) {
            const task = queue.shift();
            try {
                if (task.type === "file") {
                    await runForFile(task.obj, task.index, customVocab);
                } else {
                    await runForUrl(task.obj, task.index, customVocab);
                }
            } catch (e) {
                console.error("Task failed:", e);
            }
            updateSummary();
        }
    }

    const startTime = Date.now();

    // Chạy song song theo số luồng
    const workers = Array.from({ length: concurrency }, () => worker());
    await Promise.all(workers);

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    setRunning(false, `Đã xử lý xong toàn bộ trong <b>${duration}s</b>. Bạn có thể thêm ảnh mới.`);
}
