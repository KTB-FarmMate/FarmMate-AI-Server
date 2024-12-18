document.addEventListener("DOMContentLoaded", () => {
    let memberId = localStorage.getItem("memberId");
    if (memberId == null) {
        fetch(`${BE_SERVER}/members`, {
            method: "POST",
        })
            .then((res) => {
                if (!res.ok) {
                    return res.text().then(text => {
                        console.error(`HTTP Error ${res.status}:`, text);
                        throw new Error(`HTTP error! status: ${res.status}, message: ${text}`);
                    });
                }
                return res.json();
            })
            .then((data) => {
                localStorage.setItem("memberId", data["memberId"]);
                memberId = data["memberId"];
            })
            .catch((error) => {
                alert(error);
                console.error("MemberId CREATE Fetch error:", error);
            });

        fetch(`${BE_SERVER}/crops`)
            .then((res) => {
                if (!res.ok) {
                    return res.text().then(text => {
                        console.error(`HTTP Error ${res.status}:`, text);
                        throw new Error(`HTTP error! status: ${res.status}, message: ${text}`);
                    });
                }
                return res.json();
            })
            .then(data => {
                let crops_data = {}
                data.forEach(item => {
                    crops_data[item.cropName] = {'cropId': item.cropId, 'created': false, 'threadId': '', 'address': ''}
                });
                localStorage.setItem("crops_data", JSON.stringify(crops_data));
            }).catch(error => {
            alert(error);
            console.error("Crop Fetch error:", error);
        })
    }
    if (memberId != null) {

        setTimeout(() => {
            if (localStorage.getItem("crops") == null) {
                location.href = `./members/${memberId}/recommend`;
            } else {
                location.href = `./members/${memberId}`;
            }
        }, 2000);
    }else{
        alert("멤버 아이디가 올바르게 생성되지 않았습니다.");
        window.location.reload();
    }
});