$(document).ready(function () {
  console.log("Hlo")
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
      const $newRow = $(
        '<div class="d-flex flex-row mt-2 gap-3" style="padding-left:20px;"></div>'
      );
  
      const newContent = `
            
                  <div style="display: flex; flex-direction: row; gap: 10px;">
                    
                    <select class="form-select bg-dark" style="color: aliceblue;" aria-label="Default select example" name="system_name">
                        <option selected>Select System Name</option>
                        <option value="LMS">LMS</option>
                        <option value="PF">PF</option>
                        <option value="Insurance">Insurance</option>
                        <option value="GF">GF</option>
                    </select>
                
                    <!-- File Input and Label -->
                    <input type="file" name="file" id="file" class="inputfile" data-multiple-caption="{count} files selected" multiple>
                    <label for="file" style="text-align: center; width: 350px;"><span>Choose a file</span></label>
                
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
  
  