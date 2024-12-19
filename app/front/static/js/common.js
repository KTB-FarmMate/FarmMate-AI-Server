const BE_SERVER = "https://api.farmmate.net"
// const BE_SERVER = "http://43.202.163.157:8080"
async function fetchWithRetry(url, options = {}, maxRetries = 5, delay = 500, sync = false) {
    let attempts = 0;

    const attemptFetch = async () => {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                console.warn(`HTTP error! status: ${response.status} (Attempt ${attempts + 1})`);
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            if (response.status === 204) {
                return response;
            }
            return await response.json();
        } catch (error) {
            if (attempts < maxRetries - 1) {
                attempts++;
                console.warn(`Retrying... (${attempts}/${maxRetries})`);
                await new Promise(resolve => setTimeout(resolve, delay));
                return attemptFetch();
            } else {
                throw new Error(`Max retries reached. Last error: ${error.message}`);
            }
        }
    };

    if (sync) {
        // 동기처럼 보이도록 await 사용
        for (let attempt = 0; attempt < maxRetries; attempt++) {
            try {
                return await attemptFetch();
            } catch (error) {
                console.warn(`Retrying... (${attempt + 1}/${maxRetries})`);
                if (attempt === maxRetries - 1) {
                    throw new Error(`Max retries reached. Last error: ${error.message}`);
                }
                await new Promise(resolve => setTimeout(resolve, delay)); // 비동기 지연
            }
        }
    } else {
        // 비동기 실행
        return attemptFetch();
    }
}

function get_memberId() {
    const path = window.location.pathname;
    const parts = path.split("/");
    return parts[3];
}

function get_cropName() {
    const path = window.location.pathname;
    const parts = path.split("/");
    return decodeURIComponent(parts[5]);
}

function goBack() {
    window.history.back();
}

function goHome() {
    window.location.href = `/front/members/${get_memberId()}`
}
