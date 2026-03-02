/**
 * worker.js
 * ─────────────────────────────────────────────────────────────────
 * Điều phối hàng đợi xử lý ảnh (concurrency / multi-thread queue).
 * Gọi runForFile / runForUrl từ api.js theo số luồng được cấu hình.
 * ─────────────────────────────────────────────────────────────────
 */

async function runAll() {
    // Chỉ lấy các task chưa xử lý (status = "pending")
    const pendingFiles = state.files
        .map((obj, i) => ({ type: "file", obj, index: i }))
        .filter(task => task.obj.status === "pending");

    const pendingUrls = state.urls
        .map((obj, i) => ({ type: "url", obj, index: i }))
        .filter(task => task.obj.status === "pending");

    const queue = [...pendingFiles, ...pendingUrls];

    if (queue.length === 0 || state.running) {
        if (!state.running && (state.files.length > 0 || state.urls.length > 0)) {
            showToast("Thông báo", "Tất cả ảnh đã được xử lý xong.", "success");
        }
        return;
    }

    // Đếm số lượng xử lý trong đợt này để hiện Toast chính xác
    let sessionCompleted = 0;
    let sessionFailed = 0;

    setRunning(true);

    const concurrency = parseInt(threadsInput.value) || 1;
    const customVocab = customVocabInput.value.trim();

    // Worker tiêu thụ hàng đợi
    async function worker() {
        while (queue.length > 0 && state.running) {
            const task = queue.shift();
            const oldFailed = state.failed;
            const oldCompleted = state.completed;

            try {
                if (task.type === "file") {
                    await runForFile(task.obj, task.index, customVocab);
                } else {
                    await runForUrl(task.obj, task.index, customVocab);
                }

                // Kiểm tra xem task vừa rồi thành công hay thất bại
                if (state.completed > oldCompleted) sessionCompleted++;
                if (state.failed > oldFailed) sessionFailed++;

            } catch (e) {
                console.error("Task failed:", e);
                // Trường hợp catch ở đây thường đã được setItemError xử lý bên trong runFor...
            }
            updateSummary();
        }
    }

    const startTime = Date.now();

    // Chạy song song theo số luồng
    const workers = Array.from({ length: concurrency }, () => worker());
    await Promise.all(workers);

    const isStopped = !state.running;
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    const finishedMsg = isStopped
        ? `Đã dừng xử lý sau <b>${duration}s</b>.`
        : `Đã xử lý xong <b>${sessionCompleted + sessionFailed}</b> ảnh trong <b>${duration}s</b>.`;

    setRunning(false, finishedMsg);

    if (isStopped) {
        showToast("Đã dừng", "Quá trình xử lý đã được dừng lại.", "warning");
    }

    // Hiển thị toast kết quả của đợt chạy này
    if (sessionCompleted > 0 || sessionFailed > 0) {
        const toastType = sessionFailed === 0 ? "success" : sessionCompleted > 0 ? "warning" : "error";
        const toastTitle = sessionFailed === 0 ? "Xử lý thành công" : "Xử lý hoàn tất";
        const toastMsg = `Thành công: <b>${sessionCompleted}</b>, Thất bại: <b>${sessionFailed}</b>.`;
        showToast(toastTitle, toastMsg, toastType, 5000);
    }
}
