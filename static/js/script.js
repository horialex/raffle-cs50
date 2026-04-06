document.addEventListener('DOMContentLoaded', function () {

    // Hide flash messages
    setTimeout(function () {
        let alerts = document.querySelectorAll(".alert");
        alerts.forEach(function (alert) {
            let bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 2500); // 2500 ms = 2.5 seconds

    const deleteModal = document.getElementById('deleteUserModal');

    deleteModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;

        const userId = button.getAttribute('data-user-id');
        const username = button.getAttribute('data-username');

        const form = document.getElementById('deleteUserForm');
        form.action = `/users/delete/${userId}`;

        document.getElementById('modalUsername').textContent = username;
    });

});