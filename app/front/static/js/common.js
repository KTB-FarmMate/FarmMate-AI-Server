const BE_SERVER = "https://api.farmmate.net"
// const BE_SERVER = "http://43.202.163.157:8080"
function fetchWithRetry(url, options, maxRetries = 5, delay = 1000) {
    let attempts = 0;

    function attemptFetch() {
        return fetch(url, options)
            .then((res) => {
                if (!res.ok) {
                    console.log(`Attempt ${attempts + 1}: HTTP error! status: ${res.status}`);
                    throw new Error(`HTTP error! status: ${res.status}`);
                }
                return res.json();
            })
            .catch((error) => {
                if (attempts < maxRetries - 1) {
                    attempts++;
                    console.warn(`Retrying... (${attempts}/${maxRetries})`);
                    return new Promise((resolve) => setTimeout(resolve, delay)).then(attemptFetch);
                } else {
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
