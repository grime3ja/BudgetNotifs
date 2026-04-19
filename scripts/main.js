function send_email() {
    emailjs.sendForm('service_lnim8g7', 'template_x8s44g3', "#form").then(
        (response) => {
            console.log('SUCCESS!', response.status, response.text);
        },
        (error) => {
            console.log('FAILED...', error);
        },
    );
}