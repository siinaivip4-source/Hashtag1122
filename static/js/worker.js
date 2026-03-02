/**
 * worker.js
 * ─────────────────────────────────────────────────────────────────
 * Điều phối hàng đợi xử lý ảnh (concurrency / multi-thread queue).
 * Gọi runForFile / runForUrl từ api.js theo số luồng được cấu hình.
 * ─────────────────────────────────────────────────────────────────
 */

async function runAll() {
    console.log("runAll start. state.running:", state.running);
    // Lấy các task chưa xử lý (pending) hoặc đã lỗi (error) để chạy lại
    const pendingFiles = state.files
        .map((obj, i) => ({ type: "file", obj, index: i }))
        .filter(task => task.obj.status === "pending" || task.obj.status === "error");

    const pendingUrls = state.urls
        .map((obj, i) => ({ type: "url", obj, index: i }))
        .filter(task => task.obj.status === "pending" || task.obj.status === "error");

    const queue = [...pendingFiles, ...pendingUrls];
    console.log("Queue size:", queue.length);

    if (queue.length === 0 || state.running) {
        if (!state.running && (state.files.length > 0 || state.urls.length > 0)) {
            showToast("Thông báo", "Tất cả ảnh đã được xử lý xong (hoặc không có ảnh mới).", "success");
        }
        return;
    }

    // Đếm số lượng xử lý trong đợt này để hiện Toast chính xác
    let sessionCompleted = 0;
    let sessionFailed = 0;

    setRunning(true);

    const concurrency = (threadsInput && threadsInput.value) ? parseInt(threadsInput.value) : 1;
    const customVocab = (customVocabInput && customVocabInput.value) ? customVocabInput.value.trim() : "";

    // Worker tiêu thụ hàng đợi
    async function worker() {
        while (queue.length > 0 && state.running) {
            const task = queue.shift();
            if (!task) continue;

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
                console.error("Worker task execution error:", e, task);
                // Đảm bảo task này được đánh dấu lỗi nếu chưa được xử lý
                if (task.obj.status === "processing") {
                    task.obj.status = "error";
                    task.obj.error = String(e);
                    state.failed++;
                    sessionFailed++;
                }
            } finally {
                try {
                    updateSummary();
                } catch (err) {
                    console.error("Error updating summary:", err);
                }
            }
        }
    }

    const startTime = Date.now();

    // Chạy song song theo số luồng
    try {
        const workers = Array.from({ length: concurrency }, () => worker());
        await Promise.all(workers);
    } catch (err) {
        console.error("Critical error in runAll processing:", err);
    } finally {
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
}

async function runSingleTask(type, index) {
    if (state.running) {
        showToast("Đang bận", "Vui lòng chờ quá trình hiện tại kết thúc.", "warning");
        return;
    }
    const obj = type === "file" ? state.files[index] : state.urls[index];
    if (!obj) {
        console.error("Single task object not found at index:", index);
        return;
    }

    // Reset status to allow re-run
    if (obj.status === "done") {
        if (state.completed > 0) state.completed--;
    }
    if (obj.status === "error") {
        if (state.failed > 0) state.failed--;
    }
    obj.status = "pending";

    const customVocab = (customVocabInput && customVocabInput.value) ? customVocabInput.value.trim() : "";

    try {
        if (type === "file") {
            await runForFile(obj, index, customVocab);
        } else {
            await runForUrl(obj, index, customVocab);
        }
    } catch (e) {
        console.error("Single task execution crashed:", e);
    }
    updateSummary();
}

async function retryAll() {
    if (state.running) return;

    // Reset status of all items
    state.files.forEach(f => {
        f.status = "pending";
        delete f.selectedTags; // Clear previous manual selections if re-running all
    });
    state.urls.forEach(u => {
        u.status = "pending";
        delete u.selectedTags;
    });

    state.completed = 0;
    state.failed = 0;

    refreshGallery();
    updateSummary();

    // Start running
    await runAll();
}
