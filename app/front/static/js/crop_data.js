function crop_create(crop_name) {
    let memberId = localStorage.getItem("memberId");

    // 각 input 요소의 값을 가져옴
    const address = document.querySelector("input[name='address']").value;
    const creationDate = document.querySelector("input[name='creation_date']").value;


    const crops_data = JSON.parse(localStorage.getItem("crops_data"));

    let crop_id = crops_data[crop_name].cropId;

    const body = {
        address: address,
        cropId: crop_id,
        palntedAt: creationDate,
    }

    console.log(body);

    fetch(`${BE_SERVER}/members/${memberId}/threads`, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
    })
        .then((res) => {
            if (!res.ok) {
                console.log(res);
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            return res.json();
        })
        .then((data) => {
            crops_data[crop_name].threadId = data.threadId;
            crops_data[crop_name].created = true;
            crops_data[crop_name].address = address;
            crops_data[crop_name].palntedAt = creationDate;
            // localStorage.setItem("memberId", data["memberId"]);
        })
        .catch((error) => {
            console.error("Fetch error:", error);
        });
    localStorage.setItem("select_crop", crop_name);
    location.href = `/front/crop/${crop_name}`;
}

function crop_delete(crop_name) {
    let memberId = localStorage.getItem("memberId");
    let select_crop = localStorage.getItem("select_crop");
    let crops_data = JSON.parse(localStorage.getItem("crops_data"));
    let threadId = crops_data[select_crop].threadId;
    fetch(`${BE_SERVER}/members/${memberId}/threads/${threadId}`, {
        method: "DELETE",
        headers: {
            'Content-Type': 'application/json',
        }
    })
        .then((res) => {
            if (!res.ok) {
                console.log(res);
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            return res.json();
        })
        .then(() => {
            crops_data[crop_name].created = false;
            crops_data[crop_name].threadId = '';
            alert("작물 삭제 완료");
        })
        .catch((error) => {
            console.error("Fetch error:", error);
        });
}