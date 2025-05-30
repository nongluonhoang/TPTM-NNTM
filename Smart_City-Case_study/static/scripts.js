const firstFrame = document.getElementById('firstFrame');
const videoFrame = document.getElementById('videoFrame');
const canvas = document.getElementById('lineCanvas');
const ctx = canvas.getContext('2d');
const pointCountText = document.getElementById('pointCount');
const startButton = document.getElementById('startButton');
const instruction = document.getElementById('instruction');
const violationsBody = document.getElementById('violationsBody');
let points = [];

firstFrame.onload = function () {
    canvas.width = firstFrame.width;
    canvas.height = firstFrame.height;
    canvas.style.top = firstFrame.offsetTop + 'px';
    canvas.style.left = firstFrame.offsetLeft + 'px';
};

function drawLineWithAnimation(p1, p2) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    points.forEach(point => {
        const scaledX = point.x / (firstFrame.naturalWidth / firstFrame.width);
        const scaledY = point.y / (firstFrame.naturalHeight / firstFrame.height);
        ctx.beginPath();
        ctx.arc(scaledX, scaledY, 5, 0, 2 * Math.PI);
        ctx.fillStyle = '#00FF00';
        ctx.fill();
    });

    const scaledX1 = p1.x / (firstFrame.naturalWidth / firstFrame.width);
    const scaledY1 = p1.y / (firstFrame.naturalHeight / firstFrame.height);
    const scaledX2 = p2.x / (firstFrame.naturalWidth / firstFrame.width);
    const scaledY2 = p2.y / (firstFrame.naturalHeight / firstFrame.height);

    ctx.beginPath();
    ctx.moveTo(scaledX1, scaledY1);
    ctx.lineTo(scaledX2, scaledY2);
    ctx.strokeStyle = '#00FF00';
    ctx.lineWidth = 3;
    ctx.stroke();

    startButton.disabled = false;
}

firstFrame.addEventListener('click', (event) => {
    if (points.length >= 2) return;

    const rect = firstFrame.getBoundingClientRect();
    const scaleX = firstFrame.naturalWidth / firstFrame.width;
    const scaleY = firstFrame.naturalHeight / firstFrame.height;
    const x = (event.clientX - rect.left) * scaleX;
    const y = (event.clientY - rect.top) * scaleY;

    points.push({ x, y });
    pointCountText.textContent = `${points.length}/2 điểm đã chọn`;

    if (points.length === 2) {
        const [p1, p2] = points;
        drawLineWithAnimation(p1, p2);
    } else {
        const scaledX = x / scaleX;
        const scaledY = y / scaleY;
        ctx.beginPath();
        ctx.arc(scaledX, scaledY, 5, 0, 2 * Math.PI);
        ctx.fillStyle = '#00FF00';
        ctx.fill();
    }
});

let lastViolationCount = 0;

function fetchViolations() {
    fetch(violationsUrl)
        .then(response => response.json())
        .then(data => {
            if (data.length > lastViolationCount) {
                for (let i = lastViolationCount; i < data.length; i++) {
                    const violation = data[i];
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${violation[0]}</td>
                        <td>${violation[1]}</td>
                        <td>${violation[2]}</td>
                    `;
                    violationsBody.appendChild(row);
                }
                lastViolationCount = data.length;
            }
        })
        .catch(error => console.error('Lỗi khi lấy danh sách vi phạm:', error));
}

setInterval(fetchViolations, 2000);

startButton.addEventListener('click', () => {
    console.log('Gửi tọa độ đường thẳng tới server...');
    fetch('/set_line_points', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            x1: points[0].x,
            y1: points[0].y,
            x2: points[1].x,
            y2: points[1].y
        })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Phản hồi từ server:', data);
            if (data.status === 'success') {
                console.log('Chuyển sang luồng video:', videoFeedUrl);
                firstFrame.style.display = 'none';
                videoFrame.style.display = 'block';
                videoFrame.src = videoFeedUrl;
                instruction.textContent = "Đang theo dõi giao thông để phát hiện vi phạm...";
                startButton.style.display = 'none';
                canvas.style.display = 'none';
            } else {
                console.error('Server không trả về trạng thái success:', data);
                alert('Không thể bắt đầu xử lý video. Vui lòng thử lại!');
            }
        })
        .catch(error => {
            console.error('Lỗi khi gửi tọa độ:', error);
            alert('Có lỗi xảy ra khi gửi tọa độ đường thẳng. Kiểm tra console để biết chi tiết.');
        });
});

// Gọi lần đầu để hiển thị sẵn dữ liệu nếu có
fetchViolations();
