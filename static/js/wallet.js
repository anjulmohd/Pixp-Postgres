document.getElementById("rzp-button").onclick = function (e) {
    e.preventDefault();
    let amountInput = document.getElementById("amount");
    let amountEntered = parseFloat(amountInput.value); // Get the amount entered by the user

    // Validate the amount
    if (!amountEntered || amountEntered <= 0) {
        alert("Please enter a valid amount.");
        return;
    }

    // Divide the amount by 100
    let amountInRupees = amountEntered / 100; // Convert to rupees
    console.log("Amount entered:", amountEntered); // Debugging
    console.log("Amount in rupees:", amountInRupees); // Debugging

    // Convert the amount to paise
    let amountInPaise = Math.round(amountInRupees * 100); // Convert rupees to paise
    console.log("Amount in paise:", amountInPaise); // Debugging

    fetch("{% url 'create_razorpay_order' %}", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": "{{ csrf_token }}"
        },
        body: JSON.stringify({ amount: amountInPaise }) // Send amount in paise
    })
    .then(response => response.json())
    .then(data => {
        console.log("Razorpay order response:", data); // Debugging
        let options = {
            "key": "{{ razorpay_key }}",
            "amount": amountInPaise, // Amount in paise (required for payment)
            "currency": "INR",
            "order_id": data.order_id,
            "handler": function (response) {
                console.log("Razorpay payment response:", response); // Debugging
                fetch("{% url 'razorpay_success' %}", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": "{{ csrf_token }}"
                    },
                    body: JSON.stringify({
                        razorpay_payment_id: response.razorpay_payment_id,
                        razorpay_order_id: response.razorpay_order_id,
                        razorpay_signature: response.razorpay_signature
                    })
                })
                .then(res => res.json())
                .then(result => {
                    console.log("Payment verification response:", result); // Debugging
                    if (result.status === "success") {
                        alert("Payment successful! Wallet updated.");
                        location.reload();
                    } else {
                        alert("Payment verification failed.");
                    }
                });
            },
            "prefill": {
                "name": "{{ request.user.get_full_name }}", // Prefill user's name
                "email": "{{ request.user.email }}" // Prefill user's email
            },
            "theme": {
                "color": "#3399cc"
            },
            "description": `Wallet Top-up: ₹${amountInRupees.toFixed(2)}`, // Display amount in rupees
            "notes": {
                "amount_in_rupees": `₹${amountInRupees.toFixed(2)}` // Additional note
            }
        };
        let rzp = new Razorpay(options);
        rzp.open();
    })
    .catch(error => console.error("Error:", error));
};