document.addEventListener('DOMContentLoaded', function () {
    const statusElement = document.getElementById('status');

    function fetchVerificationStatus() {
        fetch('http://localhost:5000/verification_status') // Ganti port sesuai dengan port aplikasi Register
            .then(response => {
                console.log('Response Status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Verification status:', data);
                if (data.status === 'Success') {
                    if (data.check_in && !data.check_out) {
                        statusElement.innerHTML = `
                            <p>User ID: ${data.user_id}</p>
                            <p>Status: <span style="color: green;">Check-In</span></p>
                            <p>Timestamp: ${data.timestamp}</p>
                        `;
                    } else if (data.check_out) {
                        statusElement.innerHTML = `
                            <p>User ID: ${data.user_id}</p>
                            <p>Status: <span style="color: blue;">Check-Out</span></p>
                            <p>Timestamp: ${data.timestamp}</p>
                        `;
                    }
                } else if (data.status === 'Failed') {
                    statusElement.innerHTML = `
                        <p>Status: <span style="color: red;">Failed</span></p>
                        <p>Timestamp: ${data.timestamp}</p>
                    `;
                } else {
                    statusElement.innerHTML = `
                        <p>No logs available</p>
                    `;
                }
            })
            
            .catch(error => {
                console.error('Error fetching verification status:', error);
                statusElement.innerHTML = '<p style="color: red;">Error fetching status</p>';
            });
    }

    // Lakukan fetch data setiap 5 detik
    setInterval(fetchVerificationStatus, 500);
    fetchVerificationStatus(); // Fetch data pertama kali saat halaman diload
});
