document.addEventListener("DOMContentLoaded", () => {

        if (localStorage.getItem("memberId") == null) {
            fetch(`${BE_SERVER}/members`, {
                method: "POST",
            })
                .then((res) => {
                    if (!res.ok) {
                        console.log(res);
                        throw new Error(`HTTP error! status: ${res.status}`);
                    }
                    return res.json();
                })
                .then((data) => {
                    localStorage.setItem("memberId", data["memberId"]);
                })
                .catch((error) => {
                    console.error("Fetch error:", error);
                });

            fetch(`${BE_SERVER}/crops`)
            .then((response) => {
                if (response.ok) {
                    return response.json();
                }
            })
            .then(data => {
                let crops_data = {}
                data.forEach(item => {
                    crops_data[item.cropName] = {'cropId':item.cropId, 'created' : false, 'threadId': '', 'address': ''}
                });
                localStorage.setItem("crops_data", JSON.stringify(crops_data));
            })
        }
        setTimeout(() => {
            if (localStorage.getItem("crops") == null) {
                location.href = "/front/recommend";
            } else {
                location.href = "/front/index";
            }
        }, 2000);
    });