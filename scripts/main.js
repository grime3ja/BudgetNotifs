function send_email() {
    emailjs.sendForm('service_lnim8g7', 'template_x8s44g3', "#form").then(
        (response) => {
            console.log('SUCCESS!', response.status, response.text);
            alert ("Expense logged successfully")
        },
        (error) => {
            console.log('FAILED...', error);
            alert ("An error occured", error)
        },
    );

    formData = {
        "name": document.getElementById("name").value,
        "category": document.getElementById("category").value,
        "description": document.getElementById("desc").value,
        "price": document.getElementById("price").value
    };

    fetch("/api/index", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
}