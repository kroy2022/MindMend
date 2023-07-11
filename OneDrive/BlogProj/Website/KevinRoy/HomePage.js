// Get the current month index (0-11)
        const currentMonthIndex = new Date().getMonth();

        // Define an array of month names
        const monthNames = [
          "Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ];

        // Create the calendar dynamically
        const calendarElement = document.getElementById("calendar");
        for (let i = 0; i < monthNames.length; i++) {
          const monthElement = document.createElement("div");
          monthElement.textContent = monthNames[i];
          monthElement.classList.add("month");
          if (i === currentMonthIndex) {
            monthElement.classList.add("current-month");
          }
          calendarElement.appendChild(monthElement);
        }
        