const BE_SERVER = "https://api.farmmate.net"
// const BE_SERVER = "http://43.202.163.157:8080"
function fetchWithRetry(url, options={}, maxRetries = 5, delay = 1000) {
    let attempts = 0;

    function attemptFetch() {
        return fetch(url, options)
            .then(response => {
                // HTTP 상태 코드가 200~299가 아닌 경우 에러를 던짐
                if (!response.ok) {
                    console.warn(`HTTP error! status: ${response.status} (Attempt ${attempts + 1})`);
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json(); // 정상 응답 반환
            })
            .catch(error => {
                // 네트워크 오류 또는 HTTP 오류 발생 시 재시도
                if (attempts < maxRetries - 1) {
                    attempts++;
                    console.warn(`Retrying... (${attempts}/${maxRetries})`);
                    return new Promise(resolve => setTimeout(resolve, delay)).then(attemptFetch);
                } else {
                    // 재시도 횟수 초과 시 최종 에러 처리
                    throw new Error(`Max retries reached. Last error: ${error.message}`);
                }
            });
    }

    return attemptFetch();
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
