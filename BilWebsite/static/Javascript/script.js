$(document).ready(function () {
  // Restore fields from localStorage
//   if (localStorage.getItem("rows")) {
//     $("#location").html(localStorage.getItem("rows"));
//     $("#location").find(".dropdown-toggle").dropdown(); // Re-initialize dropdowns
//   }

  // Event listener to save fields in localStorage on change
  $(document).on("change", ".inputfile", function (e) {
    
    // saveFields();
    var $label = $(this).next("label");
    var labelVal = $label.text();
    console.log(labelVal)
    var fileName = "";
    if (this.files && this.files.length > 1) {
      fileName = (this.getAttribute("data-multiple-caption") || "").replace(
        "{count}",
        this.files.length
      );
    } else {
      fileName = e.target.value.split("\\").pop();
      console.log(fileName)
    }

    if (fileName) {
      $label.find("span").text(fileName);
    } else {
      $label.text(labelVal);
    }
  });

  $("#locationAlternate").on("click", function () {
    const rowIndex = $("#location").children().length; // Ensure unique index

    const $newRow = $(
      '<div class="d-flex flex-row mt-2 gap-3" style="padding-left:20px;"></div>'
    );
    
    const newContent = `
              <div style="display: flex; flex-direction: row; gap: 12px; width:810px">
               <!-- Bank Name Select -->
                        <select class="form-select bg-dark" name="bank_name[]" id="bank_name_{{ rowIndex }}" aria-label="Bank Name" style="color: aliceblue; ">
                            <option selected disabled>Select Bank</option>
                            <option value="Bank of Bhutan">Bank of Bhutan</option>
                            <option value="Bhutan National Bank">Bhutan National Bank</option>
                        </select>
                    
                        <!-- System Name Select -->
                        <select class="form-select bg-dark" style="color: aliceblue;" aria-label="Default select example" name="system_name[]" id="system_name_{{ rowIndex }}" >
                            <option selected>Select System Name</option>
                            <option value="LMS">LMS</option>
                            <option value="PF">PF</option>
                            <option value="Insurance">Insurance</option>
                            <option value="GF">GF</option>
                        </select>
                    
                        <!-- File Input and Label -->
                        <input type="file" name="file[]" id="file_${rowIndex}" class="inputfile" data-multiple-caption="{count} files selected" multiple>
                        <label for="file_${rowIndex}" style="text-align: center; width: 340px;"><span>Choose a file</span></label>
                    
                        <!-- Button -->
                
                    <button type="button" class="btn btn-primary button-minus">-</button>
                    </div>
        `;    
    $newRow.append(newContent);
    $("#location").append($newRow);
    $("#location").find(".dropdown-toggle").dropdown();
    // saveFields();
  });

  $("#location").on("click", ".button-minus", function () {
    $(this).closest(".d-flex.flex-row").remove();
    localStorage.clear();
    // saveFields();
  });

//   function saveFields() {
//     localStorage.setItem("rows", $("#location").html());
//   }
});

document.addEventListener("DOMContentLoaded", function () {
  var dateInput = document.getElementById("dateInput");
  console.log(dateInput)
  dateInput.addEventListener("input", function () {
    var inputValue = dateInput.value;

    if (inputValue) {
      dateInput.style.paddingLeft = "0rem";
    } else {
      dateInput.style.paddingLeft = "4.2rem";
    }
  });
});

