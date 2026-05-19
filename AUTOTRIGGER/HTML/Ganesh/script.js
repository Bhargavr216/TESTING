function showSection(sectionId) {
    // Hide all sections
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => section.classList.remove('active'));

    // Show the selected section
    const activeSection = document.getElementById(sectionId);
    activeSection.classList.add('active');
}

function handleDonation(event) {
    event.preventDefault();

    const name = document.getElementById('name').value;
    const amount = document.getElementById('amount').value;
    const paymentMethod = document.getElementById('payment-method').value;

    const donationMessage = `Thank you, ${name}! You have successfully donated $${amount} using ${paymentMethod}.`;
    document.getElementById('donation-message').textContent = donationMessage;

    // Clear the form
    document.getElementById('donation-form').reset();
}
