const BE_SERVER = "https://api.farmmate.net"

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
