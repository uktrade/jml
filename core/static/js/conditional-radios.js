govuk_radios = document.getElementsByClassName("govuk-radios");
govuk_radio_conditional_fields = document.getElementsByClassName("radio-conditional-field");
govuk_radio_conditional_wrappers = document.getElementsByClassName("govuk-radios__conditional");

// Move all conditional fields into their respective radio wrappers
Array.from(govuk_radio_conditional_fields).forEach(function(govuk_radio_conditional_field) {
    govuk_rcf_classes = govuk_radio_conditional_field.classList;

    // For each class that begins with "conditional-"
    Array.from(govuk_rcf_classes).forEach(function(govuk_rcf_class) {
        if (govuk_rcf_class.startsWith("conditional-")) {
            Array.from(govuk_radio_conditional_wrappers).forEach(function(govuk_radio_conditional_wrapper) {
                govuk_radio_conditional_wrapper_form_group = govuk_radio_conditional_wrapper.getElementsByClassName("govuk-form-group")[0];
                if (govuk_radio_conditional_wrapper.id == govuk_rcf_class) {
                    govuk_radio_conditional_wrapper_form_group.appendChild(govuk_radio_conditional_field);
                }
            });
        }
    });
});

// Add conditional logic to show/hide fields
Array.from(govuk_radios).forEach(function(govuk_radio) {
    inputs = govuk_radio.getElementsByTagName("input")
    gov_radio_conditional_wrappers = govuk_radio.getElementsByClassName("govuk-radios__conditional")
    Array.from(inputs).forEach(function(input) {
        if (input.type == "radio") {
            if (input.checked) {
                govuk_radio_conditional_field_class = "conditional-" + input.name + "-" + input.value;
                Array.from(gov_radio_conditional_wrappers).forEach(function(gov_radio_conditional_wrapper) {
                    if (gov_radio_conditional_wrapper.id == govuk_radio_conditional_field_class) {
                        govuk_radio_conditional_wrapper_form_group = gov_radio_conditional_wrapper.getElementsByClassName("govuk-form-group")[0];
                        if (govuk_radio_conditional_wrapper_form_group.childElementCount > 0) {
                            gov_radio_conditional_wrapper.classList.remove("govuk-radios__conditional--hidden");
                        }
                    }
                });
            }
            input.addEventListener("click", function (event) {
                govuk_radio_conditional_field_class = "conditional-" + event.target.name + "-" + event.target.value;
                Array.from(gov_radio_conditional_wrappers).forEach(function(gov_radio_conditional_wrapper) {
                    if (event.target.checked && gov_radio_conditional_wrapper.id == govuk_radio_conditional_field_class) {
                        govuk_radio_conditional_wrapper_form_group = gov_radio_conditional_wrapper.getElementsByClassName("govuk-form-group")[0];
                        if (govuk_radio_conditional_wrapper_form_group.childElementCount > 0) {
                            gov_radio_conditional_wrapper.classList.remove("govuk-radios__conditional--hidden");
                        }
                    } else {
                        gov_radio_conditional_wrapper.classList.add("govuk-radios__conditional--hidden");
                    }
                });
            });
        }
    });

});
