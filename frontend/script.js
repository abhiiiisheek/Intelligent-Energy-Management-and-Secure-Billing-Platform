// ============================================================
// CONFIGURATION
// ============================================================

const API = window.location.origin;

let user = "";

let liveChart;


// ============================================================
// LOGIN
// ============================================================

async function login() {

  const u =
    document.getElementById("username").value.trim();

  const p =
    document.getElementById("password").value;

  if (!u || !p) {

    alert(
      "Please enter username and password."
    );

    return;
  }

  try {

    const res = await fetch(
      `${API}/login?user=${encodeURIComponent(u)}&password=${encodeURIComponent(p)}`,
      {
        method: "POST"
      }
    );

    if (res.status !== 200) {

      alert("Login failed.");

      return;
    }

    user = u;

    document
      .getElementById("loginPage")
      .classList
      .add("hidden");

    document
      .getElementById("app")
      .classList
      .remove("hidden");

    init();

  }

  catch (error) {

    console.error(
      "Login error:",
      error
    );

    alert(
      "Could not connect to the backend."
    );
  }
}

// ============================================================
// AUTHENTICATION — SIGN UP
// ============================================================

async function signup() {

  const username =
    document
      .getElementById("signupUsername")
      .value
      .trim();

  const password =
    document
      .getElementById("signupPassword")
      .value;

  const confirmPassword =
    document
      .getElementById("signupConfirmPassword")
      .value;


  // ----------------------------------------------------------
  // CLIENT-SIDE VALIDATION
  // ----------------------------------------------------------

  if (!username || !password || !confirmPassword) {

    alert(
      "Please fill in all fields."
    );

    return;
  }


  if (password !== confirmPassword) {

    alert(
      "Passwords do not match."
    );

    return;
  }


  if (username.length < 3) {

    alert(
      "Username must be at least 3 characters."
    );

    return;
  }


  if (password.length < 8) {

    alert(
      "Password must be at least 8 characters."
    );

    return;
  }


  // ----------------------------------------------------------
  // SEND SIGNUP REQUEST
  // ----------------------------------------------------------

  try {

    const response =
      await fetch(
        `${API}/signup?user=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`,
        {
          method: "POST"
        }
      );


    const data =
      await response.json();


    // --------------------------------------------------------
    // ERROR
    // --------------------------------------------------------

    if (!response.ok) {

      alert(
        data.detail ||
        "Signup failed."
      );

      return;
    }


    // --------------------------------------------------------
    // SUCCESS
    // --------------------------------------------------------

    alert(
      "Account created successfully. Please login."
    );


    // Clear fields

    document
      .getElementById("signupUsername")
      .value = "";

    document
      .getElementById("signupPassword")
      .value = "";

    document
      .getElementById("signupConfirmPassword")
      .value = "";


    // Return to login

    showLogin();

  }

  catch (error) {

    console.error(
      "Signup error:",
      error
    );

    alert(
      "Could not connect to the backend."
    );

  }

}


// ============================================================
// SHOW LOGIN
// ============================================================

function showLogin() {

  document
    .getElementById("loginForm")
    .classList
    .remove("hidden");


  document
    .getElementById("signupForm")
    .classList
    .add("hidden");

}


// ============================================================
// SHOW SIGN UP
// ============================================================

function showSignup() {

  document
    .getElementById("loginForm")
    .classList
    .add("hidden");


  document
    .getElementById("signupForm")
    .classList
    .remove("hidden");

}


// ============================================================
// NAVIGATION
// ============================================================

function showPage(id) {

  document
    .querySelectorAll(".page")
    .forEach(
      page =>
        page.classList.add("hidden")
    );

  const selectedPage =
    document.getElementById(id);

  if (selectedPage) {

    selectedPage
      .classList
      .remove("hidden");
  }


  // ----------------------------------------------------------
  // Immediately refresh relevant page data
  // ----------------------------------------------------------

  if (id === "dashboard") {

    loadDashboard();

    loadPrediction();

    loadAlerts();
  }


  if (id === "appliances") {

    loadAppliances();
  }


  if (id === "analytics") {

    loadAnalytics();
  }


  if (id === "budget") {

    loadPlan();

    loadSummary();
  }


  if (id === "blockchain") {

    loadBlockchain();
  }
}


// ============================================================
// INITIALIZATION
// ============================================================

function init() {

  // ----------------------------------------------------------
  // Initial data load
  // ----------------------------------------------------------

  updateSimulation();

  refreshData();

  loadPrediction();


  // ----------------------------------------------------------
  // LIVE SIMULATION
  //
  // One simulated hour every hour.
  // ----------------------------------------------------------

  
const SIMULATION_INTERVAL_MS = 3600000;
setInterval(
    updateSimulation,
    SIMULATION_INTERVAL_MS
  );


  // ----------------------------------------------------------
  // Persistent data refresh
  //
  // Historical data does not need to be requested every
  // second.
  // ----------------------------------------------------------

  setInterval(
    refreshData,
    10000
  );


  // ----------------------------------------------------------
  // ML prediction
  //
  // Forecasting does not need to run every second.
  // ----------------------------------------------------------

  setInterval(
    loadPrediction,
    60000
  );
}


// ============================================================
// SIMULATION LOOP
// ============================================================

async function updateSimulation() {

  if (!user) {
    return;
  }

  try {

    const response =
      await fetch(
        `${API}/step/${encodeURIComponent(user)}`
      );

    if (!response.ok) {

      console.error(
        "Simulation step failed:",
        response.status
      );

      return;
    }


    // Update only the live dashboard every second.

    await loadDashboard();

  }

  catch (error) {

    console.error(
      "Simulation update failed:",
      error
    );
  }
}


// ============================================================
// PERSISTENT DATA REFRESH
// ============================================================

async function refreshData() {

  if (!user) {
    return;
  }

  try {

    await Promise.all([

      loadAppliances(),

      loadAnalytics(),

      loadBlockchain(),

      loadPlan(),

      loadSummary(),

      loadAlerts()

    ]);

  }

  catch (error) {

    console.error(
      "Persistent data refresh failed:",
      error
    );
  }
}


// ============================================================
// DASHBOARD
// ============================================================

async function loadDashboard() {

  if (!user) {
    return;
  }

  try {

    const r =
      await fetch(
        `${API}/status/${encodeURIComponent(user)}`
      );


    if (!r.ok) {

      console.error(
        "Dashboard request failed:",
        r.status
      );

      return;
    }


    const d =
      await r.json();


    // ==========================================================
    // LIVE METRICS
    // ==========================================================

    const powerElement =
      document.getElementById("power");

    if (powerElement) {

      powerElement.innerText =
        Number(d.power || 0).toFixed(0);

    }


    const currentElement =
      document.getElementById("current");

    if (currentElement) {

      currentElement.innerText =
        Number(d.current || 0).toFixed(2);

    }


    const energyElement =
      document.getElementById("energy");

    if (energyElement) {

      energyElement.innerText =
        Number(d.energy || 0).toFixed(2);

    }


    const hourElement =
      document.getElementById("hour");

    if (hourElement) {

      hourElement.innerText =
        d.hour ?? 0;

    }


    // ==========================================================
    // LIVE ENERGY CHART
    // ==========================================================

    const canvas =
      document.getElementById("liveChart");


    if (canvas) {

      if (!Array.isArray(window.liveEnergyHistory)) {

        window.liveEnergyHistory = [];

      }


      window.liveEnergyHistory.push(
        Number(d.energy || 0)
      );


      // Keep only the latest 24 simulated hours.

      if (
        window.liveEnergyHistory.length > 24
      ) {

        window.liveEnergyHistory =
          window.liveEnergyHistory.slice(-24);

      }


      const labels =
        window.liveEnergyHistory.map(
          (_, index) =>
            `H${index + 1}`
        );


      if (canvas.chart) {

        canvas.chart.destroy();

      }


      canvas.chart =
        new Chart(
          canvas,
          {

            type: "line",

            data: {

              labels: labels,

              datasets: [

                {

                  label:
                    "Energy Consumption (kWh)",

                  data:
                    window.liveEnergyHistory,

                  tension:
                    0.35,

                  fill:
                    true,

                  borderWidth:
                    2

                }

              ]

            },


            options: {

              responsive:
                true,

              maintainAspectRatio:
                false,


              interaction: {

                intersect:
                  false,

                mode:
                  "index"

              },


              plugins: {

                legend: {

                  display:
                    true

                }

              },


              scales: {

                y: {

                  beginAtZero:
                    true,

                  title: {

                    display:
                      true,

                    text:
                      "Energy (kWh)"

                  }

                },


                x: {

                  title: {

                    display:
                      true,

                    text:
                      "Simulation Hour"

                  }

                }

              }

            }

          }
        );

    }

  }


  catch (error) {

    console.error(
      "Dashboard loading failed:",
      error
    );

  }

}
// ============================================================
// APPLIANCES
// ============================================================

async function loadAppliances() {

  if (!user) {
    return;
  }

  try {

    const r =
      await fetch(
        `${API}/status/${encodeURIComponent(user)}`
      );


    if (!r.ok) {
      return;
    }


    const d =
      await r.json();


    let html = "";


    for (const k in d.appliances) {

      const active =
        d.appliances[k];


      html += `

        <button
          class="appliance-btn ${active ? "active" : ""}"
          onclick="toggleAppliance('${escapeHtml(k)}')"
        >

          ${escapeHtml(k)}

          (${active ? "ON" : "OFF"})

        </button>

      `;
    }


    const applianceList =
      document.getElementById(
        "applianceList"
      );


    if (applianceList) {

      applianceList.innerHTML =
        html;
    }

  }

  catch (error) {

    console.error(
      "Appliance loading failed:",
      error
    );
  }
}


// ============================================================
// TOGGLE APPLIANCE
// ============================================================

async function toggleAppliance(device) {

  if (!user) {
    return;
  }

  try {

    const response =
      await fetch(
        `${API}/toggle/${encodeURIComponent(user)}/${encodeURIComponent(device)}`
      );


    if (!response.ok) {

      alert(
        "Could not toggle appliance."
      );

      return;
    }


    // Immediately update UI.

    await loadDashboard();

    await loadAppliances();

  }

  catch (error) {

    console.error(
      "Toggle error:",
      error
    );
  }
}


// ============================================================
// ADD APPLIANCE TO LIVE SIMULATION
// ============================================================

async function addAppliance() {

  const nameInput =
    document.getElementById("name");

  const powerInput =
    document.getElementById("powerInput");

  const countInput =
    document.getElementById("count");


  const n =
    nameInput
      ? nameInput.value.trim()
      : "";


  const p =
    powerInput
      ? Number(powerInput.value)
      : 0;


  const c =
    countInput
      ? Number(countInput.value)
      : 0;


  if (!n) {

    alert(
      "Please enter an appliance name."
    );

    return;
  }


  if (p <= 0) {

    alert(
      "Power must be greater than 0."
    );

    return;
  }


  if (c <= 0) {

    alert(
      "Count must be greater than 0."
    );

    return;
  }


  try {

    const r =
      await fetch(
        `${API}/add/${encodeURIComponent(user)}?name=${encodeURIComponent(n)}&power=${p}&count=${c}`,
        {
          method: "POST"
        }
      );


    if (!r.ok) {

      let errorMessage =
        "Could not add appliance.";


      try {

        const error =
          await r.json();


        errorMessage =
          error.detail ||
          errorMessage;

      }

      catch (_) {}


      alert(
        errorMessage
      );

      return;
    }


    // Clear form.

    if (nameInput) {
      nameInput.value = "";
    }

    if (powerInput) {
      powerInput.value = "";
    }

    if (countInput) {
      countInput.value = "";
    }


    await loadAppliances();

    await loadDashboard();

  }

  catch (error) {

    console.error(
      "Add appliance error:",
      error
    );

    alert(
      "Could not connect to backend."
    );
  }
}


// ============================================================
// ANALYTICS
// ============================================================

async function loadAnalytics() {

  if (!user) {
    return;
  }

  try {

    const r =
      await fetch(
        `${API}/analytics/${encodeURIComponent(user)}`
      );


    if (!r.ok) {

      console.error(
        "Analytics request failed:",
        r.status
      );

      return;
    }


    const d =
      await r.json();


    // --------------------------------------------------------
    // Hourly chart
    // --------------------------------------------------------

    draw(
      "hourlyChart",
      d.hourly || []
    );


    // --------------------------------------------------------
    // Weekly chart
    // --------------------------------------------------------

    drawBar(
      "weeklyChart",
      d.weekly || [],
      "Week"
    );


    // --------------------------------------------------------
    // Monthly chart
    // --------------------------------------------------------

    drawBar(
      "monthlyChart",
      d.monthly || [],
      "Month"
    );


    // --------------------------------------------------------
    // Calculate total energy
    // --------------------------------------------------------

    const dailyData =
      d.daily || [];


    const totalEnergy =
      dailyData.reduce(
        (sum, value) =>
          sum + Number(value || 0),
        0
      );


    // --------------------------------------------------------
    // Latest billing record
    // --------------------------------------------------------

    const billing =
      d.billing || [];


    const latestBilling =
      billing.length > 0
        ? billing[billing.length - 1]
        : null;


    // --------------------------------------------------------
    // Analytics summary cards
    // --------------------------------------------------------

    const analyticsSummary =
      document.getElementById(
        "analyticsSummary"
      );


    if (analyticsSummary) {

      const expected =
        latestBilling
          ? Number(
              latestBilling.expected
            )
          : null;


      const actual =
        latestBilling
          ? Number(
              latestBilling.actual
            )
          : null;


      let budgetStatus =
        "No billing data yet";


      if (
        expected !== null &&
        actual !== null
      ) {

        if (actual <= expected) {

          budgetStatus =
            "Within Budget";

        }

        else {

          budgetStatus =
            "Over Budget";
        }
      }


      analyticsSummary.innerHTML = `

        <div class="card">

          <h3>Total Energy</h3>

          <p>
            ${totalEnergy.toFixed(2)}
            kWh
          </p>

        </div>


        <div class="card">

          <h3>Days Recorded</h3>

          <p>
            ${dailyData.length}
          </p>

        </div>


        <div class="card">

          <h3>Latest Monthly Bill</h3>

          <p>

            ${
              actual !== null
                ? "₹" +
                  actual.toFixed(2)
                : "No data"
            }

          </p>

        </div>


        <div class="card">

          <h3>Monthly Budget</h3>

          <p>

            ${
              expected !== null
                ? "₹" +
                  expected.toFixed(2)
                : "No data"
            }

          </p>

        </div>


        <div class="card">

          <h3>Budget Status</h3>

          <p>
            ${budgetStatus}
          </p>

        </div>

      `;
    }

  }

  catch (error) {

    console.error(
      "Analytics loading failed:",
      error
    );
  }
}


// ============================================================
// LINE CHART
// ============================================================

function draw(
  id,
  data
) {

  const canvas =
    document.getElementById(id);


  if (!canvas) {
    return;
  }


  if (!Array.isArray(data)) {
    data = [];
  }


  if (canvas.chart) {

    canvas.chart.destroy();
  }


  canvas.chart =
    new Chart(
      canvas,
      {

        type: "line",


        data: {

          labels:
            data.map(
              (_, i) =>
                i + 1
            ),


          datasets: [

            {

              label:
                "Energy (kWh)",

              data:
                data,

              tension:
                0.2,

              fill:
                false

            }

          ]

        },


        options: {

          responsive:
            true,

          maintainAspectRatio:
            true,


          scales: {

            y: {

              beginAtZero:
                true,

              title: {

                display:
                  true,

                text:
                  "Energy (kWh)"

              }

            },


            x: {

              title: {

                display:
                  true,

                text:
                  "Hour"

              }

            }

          }

        }

      }
    );
}


// ============================================================
// BAR CHART
// ============================================================

function drawBar(
  id,
  data,
  type
) {

  const canvas =
    document.getElementById(id);


  if (!canvas) {
    return;
  }


  if (!Array.isArray(data)) {
    data = [];
  }


  const labels =
    data.map(
      (_, i) => {

        if (
          type === "Week"
        ) {

          return (
            `Week ${i + 1}`
          );
        }


        const months = [

          "Jan",
          "Feb",
          "Mar",
          "Apr",
          "May",
          "Jun",
          "Jul",
          "Aug",
          "Sep",
          "Oct",
          "Nov",
          "Dec"

        ];


        return (
          months[i] ||
          `Month ${i + 1}`
        );

      }
    );


  if (canvas.chart) {

    canvas.chart.destroy();
  }


  canvas.chart =
    new Chart(
      canvas,
      {

        type: "bar",


        data: {

          labels:
            labels,


          datasets: [

            {

              label:
                "Energy (kWh)",

              data:
                data

            }

          ]

        },


        options: {

          responsive:
            true,

          maintainAspectRatio:
            true,


          scales: {

            y: {

              beginAtZero:
                true,

              title: {

                display:
                  true,

                text:
                  "Energy (kWh)"

              }

            },


            x: {

              title: {

                display:
                  true,

                text:
                  type

              }

            }

          }

        }

      }
    );
}


// ============================================================
// BLOCKCHAIN
// ============================================================

async function loadBlockchain() {

  if (!user) {
    return;
  }

  const chain =
    document.getElementById("chain");

  if (!chain) {
    console.warn(
      "Blockchain container (#chain) not found."
    );
    return;
  }

  try {

    const response =
      await fetch(
        `${API}/blockchain/${encodeURIComponent(user)}`,
        {
          method: "GET",

          headers: {
            "Accept": "application/json"
          },

          cache: "no-store"
        }
      );


    // ==========================================================
    // HTTP ERROR
    // ==========================================================

    if (!response.ok) {

      chain.innerHTML = `
        <div class="card blockchain-empty">

          <h3>
            Blockchain Unavailable
          </h3>

          <p>
            Could not load blockchain records.
          </p>

          <p>
            Server response:
            <strong>
              ${response.status}
            </strong>
          </p>

        </div>
      `;

      console.error(
        "Blockchain request failed:",
        response.status,
        response.statusText
      );

      return;
    }


    // ==========================================================
    // PARSE RESPONSE
    // ==========================================================

    const data =
      await response.json();


    // ==========================================================
    // VALIDATE RESPONSE
    // ==========================================================

    if (!Array.isArray(data)) {

      chain.innerHTML = `
        <div class="card blockchain-empty">

          <h3>
            Invalid Blockchain Data
          </h3>

          <p>
            The backend did not return a valid
            blockchain array.
          </p>

        </div>
      `;

      console.error(
        "Invalid blockchain response:",
        data
      );

      return;
    }


    // ==========================================================
    // EMPTY BLOCKCHAIN
    // ==========================================================

    if (data.length === 0) {

      chain.innerHTML = `
        <div class="blockchain-empty">

          <h3>
            No Blockchain Records
          </h3>

          <p>
            No billing records have been added
            to the blockchain yet.
          </p>

        </div>
      `;

      return;
    }


    // ==========================================================
    // CHAIN VALIDATION
    // ==========================================================

    const validBlocks =
      data.filter(
        block =>
          block.valid === true
      ).length;


    const invalidBlocks =
      data.length - validBlocks;


    const invalidHashes =
      data.filter(
        block =>
          block.hash_valid !== true
      ).length;


    const invalidLinks =
      data.filter(
        block =>
          block.linkage_valid !== true
      ).length;


    const chainValid =
      invalidBlocks === 0 &&
      invalidHashes === 0 &&
      invalidLinks === 0;


    // ==========================================================
    // INTEGRITY PANEL
    // ==========================================================

    chain.innerHTML = `

      <div class="
        blockchain-integrity
        ${chainValid ? "valid" : "invalid"}
      ">

        <div class="integrity-header">

          <div>

            <h3 class="integrity-title">
              Blockchain Integrity
            </h3>

            <p>
              ${validBlocks} / ${data.length}
              blocks verified
            </p>

          </div>


          <div class="
            integrity-status
            ${chainValid ? "" : "invalid"}
          ">

            ${
              chainValid
                ? "VALID"
                : "TAMPERED"
            }

          </div>

        </div>


        <div class="blockchain-stats">


          <div class="blockchain-stat">

            <span class="blockchain-stat-label">
              Total Blocks
            </span>

            <span class="blockchain-stat-value">
              ${data.length}
            </span>

          </div>


          <div class="blockchain-stat">

            <span class="blockchain-stat-label">
              Valid Blocks
            </span>

            <span class="blockchain-stat-value">
              ${validBlocks}
            </span>

          </div>


          <div class="blockchain-stat">

            <span class="blockchain-stat-label">
              Invalid Hashes
            </span>

            <span class="blockchain-stat-value">
              ${invalidHashes}
            </span>

          </div>


          <div class="blockchain-stat">

            <span class="blockchain-stat-label">
              Broken Links
            </span>

            <span class="blockchain-stat-value">
              ${invalidLinks}
            </span>

          </div>


        </div>

      </div>


      <div class="blockchain-ledger">

        ${
          data.map(
            (block, index) => {

              const blockValid =
                block.valid === true;

              const hashValid =
                block.hash_valid === true;

              const linkageValid =
                block.linkage_valid === true;


              return `

                <div class="blockchain-block">


                  <!-- ==========================================
                       BLOCK HEADER
                  =========================================== -->

                  <div class="block-header">

                    <div>

                      <div class="block-number">
                        Block #${escapeHtml(
                          String(block.day)
                        )}
                      </div>

                      <div class="block-date">
                        ${escapeHtml(
                          String(block.date)
                        )}
                      </div>

                    </div>


                    <div class="
                      block-verified
                      ${
                        blockValid
                          ? ""
                          : "block-invalid"
                      }
                    ">

                      ${
                        blockValid
                          ? "VERIFIED"
                          : "INVALID"
                      }

                    </div>

                  </div>


                  <!-- ==========================================
                       BILLING METRICS
                  =========================================== -->

                  <div class="block-metrics">


                    <div class="block-metric">

                      <span class="block-metric-label">
                        Energy
                      </span>

                      <span class="block-metric-value">
                        ${Number(
                          block.energy
                        ).toFixed(2)}
                        kWh
                      </span>

                    </div>


                    <div class="block-metric">

                      <span class="block-metric-label">
                        Electricity Bill
                      </span>

                      <span class="block-metric-value">
                        ₹${Number(
                          block.bill
                        ).toFixed(2)}
                      </span>

                    </div>


                  </div>


                  <!-- ==========================================
                       PREVIOUS HASH
                  =========================================== -->

                  <div class="hash-section">

                    <span class="hash-label">
                      Previous Hash
                    </span>

                    <code class="hash-value">
                      ${escapeHtml(
                        String(
                          block.prev_hash
                        )
                      )}
                    </code>

                  </div>


                  <!-- ==========================================
                       CURRENT HASH
                  =========================================== -->

                  <div class="hash-section">

                    <span class="hash-label">
                      Current Hash
                    </span>

                    <code class="hash-value">
                      ${escapeHtml(
                        String(
                          block.hash
                        )
                      )}
                    </code>

                  </div>


                  <!-- ==========================================
                       CALCULATED HASH
                  =========================================== -->

                  <div class="hash-section">

                    <span class="hash-label">
                      Calculated Hash
                    </span>

                    <code class="hash-value">
                      ${escapeHtml(
                        String(
                          block.calculated_hash
                        )
                      )}
                    </code>

                  </div>


                  <!-- ==========================================
                       VALIDATION
                  =========================================== -->

                  <div class="validation-details">


                    <p class="${
                      hashValid
                        ? "validation-ok"
                        : "validation-error"
                    }">

                      ${
                        hashValid
                          ? "Hash verified"
                          : "Hash verification failed"
                      }

                    </p>


                    <p class="${
                      linkageValid
                        ? "validation-ok"
                        : "validation-error"
                    }">

                      ${
                        linkageValid
                          ? "Previous block linked"
                          : "Previous block linkage broken"
                      }

                    </p>


                  </div>


                </div>


                ${
                  index < data.length - 1
                    ? `
                      <div class="blockchain-connector">
                        |
                      </div>
                    `
                    : ""
                }

              `;

            }
          ).join("")
        }

      </div>

    `;

  }


  // ==========================================================
  // ERROR HANDLING
  // ==========================================================

  catch (error) {

    console.error(
      "Blockchain loading failed:",
      error
    );


    chain.innerHTML = `

      <div class="card blockchain-empty">

        <h3>
          Blockchain Loading Error
        </h3>

        <p>
          ${escapeHtml(
            error.message ||
            "Unable to load blockchain data."
          )}
        </p>

      </div>

    `;

  }

}
// ============================================================
// PLAN
// ============================================================

async function loadPlan() {

  if (!user) {
    return;
  }

  try {

    const r =
      await fetch(
        `${API}/plan/${encodeURIComponent(user)}`
      );


    if (!r.ok) {
      return;
    }


    const d =
      await r.json();


    const planBox =
      document.getElementById(
        "planBox"
      );


    if (!planBox) {
      return;
    }


    const plans =
      Array.isArray(d.plan)
        ? d.plan
        : [];


    planBox.innerHTML =
      plans.length

        ? plans
            .map(
              p => {

                const lines =
                  String(p)
                    .split("\n")
                    .filter(
                      line =>
                        line.trim()
                    );

                return lines
                  .map(
                    line =>
                      `<p>${escapeHtml(line)}</p>`
                  )
                  .join("");

              }
            )
            .join("")

        : "<p>No plan generated yet.</p>";

  }

  catch (error) {

    console.error(
      "Plan loading failed:",
      error
    );
  }
}


// ============================================================
// SUMMARY
// ============================================================

async function loadSummary() {

  if (!user) {
    return;
  }

  try {

    const r =
      await fetch(
        `${API}/summary/${encodeURIComponent(user)}`
      );


    if (!r.ok) {
      return;
    }


    const d =
      await r.json();


    const summary =
      document.getElementById(
        "summary"
      );


    if (!summary) {
      return;
    }


    if (!Array.isArray(d) || d.length === 0) {

      summary.innerHTML =
        "<p>No monthly summary yet.</p>";

      return;
    }


    summary.innerHTML =
      d.map(
        m => `

          <div class="card">

            <p>
              Month ${escapeHtml(
                m.month
              )}
            </p>

            <p>
              Expected:
              ₹${Number(
                m.expected
              ).toFixed(2)}
            </p>

            <p>
              Actual:
              ₹${Number(
                m.actual
              ).toFixed(2)}
            </p>

          </div>

        `
      ).join("");

  }

  catch (error) {

    console.error(
      "Summary loading failed:",
      error
    );
  }
}


// ============================================================
// BUDGET
// ============================================================

async function setBudget() {

  const budgetInput =
    document.getElementById(
      "budgetInput"
    );


  const val =
    budgetInput
      ? Number(
          budgetInput.value
        )
      : 0;


  if (val <= 0) {

    alert(
      "Please enter a valid budget."
    );

    return;
  }


  try {

    const r =
      await fetch(
        `${API}/budget/${encodeURIComponent(user)}/${val}`,
        {
          method: "POST"
        }
      );


    if (!r.ok) {

      alert(
        "Could not update budget."
      );

      return;
    }


    alert(
      "Monthly budget updated."
    );


    if (budgetInput) {
      budgetInput.value = "";
    }


    await loadSummary();

    await loadAnalytics();

  }

  catch (error) {

    console.error(
      "Budget update failed:",
      error
    );

    alert(
      "Could not connect to backend."
    );
  }
}


// ============================================================
// ALERTS
// ============================================================

async function loadAlerts() {

  if (!user) {
    return;
  }

  try {

    const r =
      await fetch(
        `${API}/alerts/${encodeURIComponent(user)}`
      );


    if (!r.ok) {
      return;
    }


    const d =
      await r.json();


    const alerts =
      document.getElementById(
        "alerts"
      );


    if (alerts) {

      alerts.innerText =
        d.msg || "No alerts.";
    }

  }

  catch (error) {

    console.error(
      "Alerts loading failed:",
      error
    );
  }
}


// ============================================================
// ML PREDICTION
// ============================================================

async function loadPrediction() {

  if (!user) {
    return;
  }

  const prediction =
    document.getElementById("prediction");

  const meta =
    document.getElementById("predictionMeta");

  if (!prediction) {
    return;
  }

  try {

    const response =
      await fetch(
        `${API}/household-forecast/${encodeURIComponent(user)}`,
        {
          method: "GET",

          headers: {
            "Accept": "application/json"
          },

          cache: "no-store"
        }
      );

    if (!response.ok) {

      throw new Error(
        `HTTP ${response.status}`
      );

    }

    const data =
      await response.json();

    /*
     * --------------------------------------------------------
     * NEXT-HOUR FORECAST
     * --------------------------------------------------------
     */

    prediction.innerHTML = `

      <div class="forecast-primary">

        <span>
          Next-hour demand
        </span>

        <strong>
          ${Number(
            data.next_hour_kwh || 0
          ).toFixed(3)}
          kWh
        </strong>

      </div>

    `;

    /*
     * --------------------------------------------------------
     * FORECAST DETAILS
     * --------------------------------------------------------
     */

    if (meta) {

      meta.innerHTML = `

        <div class="forecast-grid">

          <div class="forecast-item">

            <span>
              Next 6 hours
            </span>

            <strong>
              ${Number(
                data.next_6_hours_kwh || 0
              ).toFixed(2)}
              kWh
            </strong>

          </div>


          <div class="forecast-item">

            <span>
              Consumed today
            </span>

            <strong>
              ${Number(
                data.consumed_today_kwh || 0
              ).toFixed(2)}
              kWh
            </strong>

          </div>


          <div class="forecast-item">

            <span>
              Remaining today
            </span>

            <strong>
              ${Number(
                data.remaining_today_kwh || 0
              ).toFixed(2)}
              kWh
            </strong>

          </div>


          <div class="forecast-item">

            <span>
              Projected today
            </span>

            <strong>
              ${Number(
                data.projected_daily_kwh || 0
              ).toFixed(2)}
              kWh
            </strong>

          </div>


          <div class="forecast-item">

            <span>
              Projected bill
            </span>

            <strong>
              ₹${Number(
                data.projected_daily_bill || 0
              ).toFixed(2)}
            </strong>

          </div>


          <div class="forecast-item">

            <span>
              Current load
            </span>

            <strong>
              ${Number(
                data.current_power_w || 0
              ).toFixed(0)}
              W
            </strong>

          </div>

        </div>


        <div class="forecast-footer">

          Based on
          ${Number(
            data.history_hours || 0
          )}
          hours of household data

          <br>

          Simulation hour:
          ${Number(
            data.current_hour || 0
          )}

          <br>

          Method:
          ${escapeHtml(
            String(
              data.method ||
              "Household forecast"
            )
          )}

        </div>

      `;

    }

  }

  catch (error) {

    console.error(
      "Household forecast failed:",
      error
    );

    prediction.innerText =
      "Household forecast unavailable.";

    if (meta) {

      meta.innerText =
        "Waiting for household consumption data.";

    }

  }

}


// ============================================================
// ENERGY ESTIMATOR
// ============================================================

function addEstimateAppliance(
  name = "",
  power = "",
  count = 1,
  hours = ""
) {

  const container =
    document.getElementById(
      "estimateAppliances"
    );


  if (!container) {
    return;
  }


  const row =
    document.createElement(
      "div"
    );


  row.className =
    "estimate-row";


  row.innerHTML = `

    <input
      type="text"
      class="estimate-name"
      placeholder="Appliance"
      value="${escapeHtml(name)}"
    >


    <input
      type="number"
      class="estimate-power"
      placeholder="Power (W)"
      min="1"
      value="${power}"
    >


    <input
      type="number"
      class="estimate-count"
      placeholder="Quantity"
      min="1"
      value="${count}"
    >


    <input
      type="number"
      class="estimate-hours"
      placeholder="Hours/day"
      min="0"
      max="24"
      step="0.5"
      value="${hours}"
    >


    <button
      type="button"
      onclick="this.parentElement.remove()"
    >
      Remove
    </button>

  `;


  container.appendChild(
    row
  );
}


// ============================================================
// CALCULATE HOUSEHOLD ENERGY
// ============================================================

async function calculateEstimate() {

  const householdSize =
    Number(
      document.getElementById(
        "householdSize"
      ).value
    );


  const rows =
    document.querySelectorAll(
      ".estimate-row"
    );


  if (
    !householdSize ||
    householdSize <= 0
  ) {

    alert(
      "Please enter a valid household size."
    );

    return;
  }


  if (rows.length === 0) {

    alert(
      "Please add at least one appliance."
    );

    return;
  }


  const appliances = [];


  for (const row of rows) {

    const name =
      row.querySelector(
        ".estimate-name"
      ).value.trim();


    const power =
      Number(
        row.querySelector(
          ".estimate-power"
        ).value
      );


    const count =
      Number(
        row.querySelector(
          ".estimate-count"
        ).value
      );


    const hours =
      Number(
        row.querySelector(
          ".estimate-hours"
        ).value
      );


    if (!name) {

      alert(
        "Please enter an appliance name."
      );

      return;
    }


    if (
      !power ||
      power <= 0
    ) {

      alert(
        `Invalid power for ${name}.`
      );

      return;
    }


    if (
      !count ||
      count <= 0
    ) {

      alert(
        `Invalid quantity for ${name}.`
      );

      return;
    }


    if (
      hours < 0 ||
      hours > 24
    ) {

      alert(
        `Hours/day for ${name} must be between 0 and 24.`
      );

      return;
    }


    appliances.push({

      name:
        name,

      power:
        power,

      count:
        count,

      hours_per_day:
        hours

    });
  }


  const requestBody = {

    household_size:
      householdSize,

    appliances:
      appliances

  };


  try {

    const response =
      await fetch(
        `${API}/estimate`,
        {

          method:
            "POST",

          headers: {

            "Content-Type":
              "application/json"

          },

          body:
            JSON.stringify(
              requestBody
            )

        }
      );


    if (!response.ok) {

      let errorMessage =
        "Energy estimation failed.";


      try {

        const error =
          await response.json();


        errorMessage =
          error.detail ||
          errorMessage;

      }

      catch (_) {}


      alert(
        errorMessage
      );

      return;
    }


    const data =
      await response.json();


    // --------------------------------------------------------
    // TOTALS
    // --------------------------------------------------------

    const estimatedDaily =
      document.getElementById(
        "estimatedDaily"
      );


    if (estimatedDaily) {

      estimatedDaily.innerText =
        Number(
          data.daily_consumption_kwh
        ).toFixed(2);
    }


    const estimatedMonthly =
      document.getElementById(
        "estimatedMonthly"
      );


    if (estimatedMonthly) {

      estimatedMonthly.innerText =
        Number(
          data.monthly_consumption_kwh
        ).toFixed(2);
    }


    const estimatedBill =
      document.getElementById(
        "estimatedBill"
      );


    if (estimatedBill) {

      estimatedBill.innerText =
        Number(
          data.estimated_monthly_bill
        ).toFixed(2);
    }


    // --------------------------------------------------------
    // APPLIANCE BREAKDOWN
    // --------------------------------------------------------

    const breakdown =
      document.getElementById(
        "estimateBreakdown"
      );


    if (breakdown) {

      breakdown.innerHTML =
        data.appliances
          .map(
            appliance => `

              <div class="card">

                <h4>
                  ${escapeHtml(
                    appliance.name
                  )}
                </h4>


                <p>
                  Power:
                  ${appliance.power_watts}
                  W
                </p>


                <p>
                  Quantity:
                  ${appliance.count}
                </p>


                <p>
                  Usage:
                  ${appliance.hours_per_day}
                  hrs/day
                </p>


                <p>
                  Daily:
                  <strong>
                    ${appliance.daily_kwh}
                    kWh
                  </strong>
                </p>


                <p>
                  Monthly:
                  <strong>
                    ${appliance.monthly_kwh}
                    kWh
                  </strong>
                </p>

              </div>

            `
          )
          .join("");
    }


    const estimateResult =
      document.getElementById(
        "estimateResult"
      );


    if (estimateResult) {

      estimateResult
        .classList
        .remove("hidden");
    }

  }

  catch (error) {

    console.error(
      "Energy estimation error:",
      error
    );


    alert(
      "Could not connect to the backend."
    );
  }
}


// ============================================================
// DEFAULT ESTIMATE APPLIANCES
// ============================================================

function initializeEstimateAppliances() {

  const container =
    document.getElementById(
      "estimateAppliances"
    );


  if (!container) {
    return;
  }


  // Prevent duplicate rows.

  if (
    container.children.length > 0
  ) {

    return;
  }


  addEstimateAppliance(
    "AC",
    1500,
    1,
    6
  );


  addEstimateAppliance(
    "Fan",
    75,
    3,
    8
  );


  addEstimateAppliance(
    "TV",
    100,
    1,
    4
  );
}


// ============================================================
// SIMPLE HTML ESCAPING
// ============================================================

function escapeHtml(value) {

  return String(value)

    .replace(
      /&/g,
      "&amp;"
    )

    .replace(
      /</g,
      "&lt;"
    )

    .replace(
      />/g,
      "&gt;"
    )

    .replace(
      /"/g,
      "&quot;"
    )

    .replace(
      /'/g,
      "&#039;"
    );
}


// ============================================================
// INITIALIZE ESTIMATOR
// ============================================================

document.addEventListener(
  "DOMContentLoaded",
  () => {

    initializeEstimateAppliances();

  }
);







