document.addEventListener('DOMContentLoaded', function () {
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