document.addEventListener('DOMContentLoaded', function () {

    // Hide flash messages
    // setTimeout(function () {
    //     let alerts = document.querySelectorAll(".alert");
    //     alerts.forEach(function (alert) {
    //         let bsAlert = new bootstrap.Alert(alert);
    //         bsAlert.close();
    //     });
    // }, 2000); // 2000 ms = 2 seconds

    const deleteModal = document.getElementById('deleteUserModal');

    deleteModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;

        const userId = button.getAttribute('data-user-id');
        const username = button.getAttribute('data-username');

        const form = document.getElementById('deleteUserForm');
        form.action = `/delete/${userId}`;

        document.getElementById('modalUsername').textContent = username;
    });

});