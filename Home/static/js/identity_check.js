document.addEventListener(
    "DOMContentLoaded",
    async function () {

        const video =
            document.getElementById(
                "video"
            );

        const canvas =
            document.getElementById(
                "canvas"
            );

        const result =
            document.getElementById(
                "result"
            );

        const cameraStatus =
            document.getElementById(
                "camera-status"
            );

        const examId =
            document.getElementById(
                "exam-id"
            ).value;

        try {

            const stream =
                await navigator
                    .mediaDevices
                    .getUserMedia({
                        video: true
                    });

            video.srcObject =
                stream;

            cameraStatus.innerHTML =
            `
            <span
            style="
                width:12px;
                height:12px;
                border-radius:50%;
                background:#2ecc71;
                display:inline-block;
            ">
            </span>

            Camera Ready
            `;

        } catch {

            cameraStatus.innerHTML =
            `
            <span
            style="
                width:12px;
                height:12px;
                border-radius:50%;
                background:#ff6b6b;
                display:inline-block;
            ">
            </span>

            Camera Access Failed
            `;

            cameraStatus.style.background =
                "rgba(231,76,60,0.15)";

            cameraStatus.style.color =
                "#ff6b6b";

            result.innerText =
                "Camera access denied.";

            return;
        }

        document
            .getElementById(
                "verify-btn"
            )
            .addEventListener(
                "click",
                async function () {

                    cameraStatus.innerHTML =
                    `
                    <span
                    style="
                        width:12px;
                        height:12px;
                        border-radius:50%;
                        background:#ffd369;
                        display:inline-block;
                    ">
                    </span>

                    Verifying Identity...
                    `;

                    canvas.width =
                        video.videoWidth;

                    canvas.height =
                        video.videoHeight;

                    const ctx =
                        canvas.getContext(
                            "2d"
                        );

                    ctx.drawImage(
                        video,
                        0,
                        0
                    );

                    const image =
                        canvas.toDataURL(
                            "image/jpeg"
                        );

                    try {

                        const response =
                            await fetch(
                                "/verify-identity/",
                                {
                                    method:
                                    "POST",

                                    headers: {
                                        "Content-Type":
                                        "application/json",

                                        "X-CSRFToken":
                                        getCookie(
                                            "csrftoken"
                                        )
                                    },

                                    body:
                                    JSON.stringify({
                                        image
                                    })
                                }
                            );

                        const data =
                            await response.json();

                        if (
                            data.verified
                        ) {

                            cameraStatus.innerHTML =
                            `
                            <span
                            style="
                                width:12px;
                                height:12px;
                                border-radius:50%;
                                background:#2ecc71;
                                display:inline-block;
                            ">
                            </span>

                            Identity Verified
                            `;

                            result.innerText =
                                `Similarity: ${data.similarity}`;

                            setTimeout(
                                function () {

                                    window.location.href =
                                        `/test/${examId}/`;

                                },
                                1500
                            );

                        } else {

                            cameraStatus.innerHTML =
                            `
                            <span
                            style="
                                width:12px;
                                height:12px;
                                border-radius:50%;
                                background:#ff6b6b;
                                display:inline-block;
                            ">
                            </span>

                            Verification Failed
                            `;

                            result.innerText =
                                `Similarity: ${
                                    data.similarity || 0
                                }`;
                        }

                    } catch {

                        cameraStatus.innerHTML =
                        `
                        <span
                        style="
                            width:12px;
                            height:12px;
                            border-radius:50%;
                            background:#ff6b6b;
                            display:inline-block;
                        ">
                        </span>

                        Server Error
                        `;

                        result.innerText =
                            "Unable to verify identity.";
                    }
                }
            );
    }
);

function getCookie(name) {

    let cookieValue = null;

    if (
        document.cookie &&
        document.cookie !== ""
    ) {

        const cookies =
            document.cookie.split(";");

        for (
            let i = 0;
            i < cookies.length;
            i++
        ) {

            const cookie =
                cookies[i].trim();

            if (
                cookie.substring(
                    0,
                    name.length + 1
                ) ===
                (name + "=")
            ) {

                cookieValue =
                    decodeURIComponent(
                        cookie.substring(
                            name.length + 1
                        )
                    );

                break;
            }
        }
    }

    return cookieValue;
}