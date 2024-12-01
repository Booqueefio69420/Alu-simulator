from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# Initialize 16 registers, each 16 bits
registers = [0] * 16  # Default values are all 0

# ALU operation decoder
OPCODE_DESCRIPTIONS = {
    "0000": "ADD (Add A + B -> C)",
    "0001": "SUB (Subtract A - B -> C)",
    "0010": "MUL (Multiply A * B -> C)",
    "0011": "AND (Bitwise AND A & B -> C)",
    "0100": "OR (Bitwise OR A | B -> C)",
    "0101": "XOR (Bitwise XOR A ^ B -> C)",
    "0110": "NOT (Bitwise NOT A -> C)",
    "1111": "Load Immediate (Immediate -> A)"
}

def simulate_alu(opcode, A, B, C):
    # Fetch register values
    X = registers[A]
    Y = registers[B]
    Z = 0

    # Perform ALU operations based on opcode
    if opcode == 0b0000:  # ADD
        Z = X + Y
    elif opcode == 0b0001:  # SUB
        Z = X - Y
    elif opcode == 0b0010:  # MUL
        Z = X * Y
    elif opcode == 0b0011:  # AND
        Z = X & Y
    elif opcode == 0b0100:  # OR
        Z = X | Y
    elif opcode == 0b0101:  # XOR
        Z = X ^ Y
    elif opcode == 0b0110:  # NOT
        Z = ~X & 0xFFFF  # Ensure 16-bit result
    elif opcode == 0b1111:  # Load Immediate
        registers[A] = B  # Treat B as the immediate value
        Z = registers[A]
    else:
        Z = 0  # Invalid opcode

    # Write the result to the destination register (if applicable)
    if opcode != 0b1111:  # Exclude Load Immediate
        registers[C] = Z & 0xFFFF  # Ensure 16-bit result

    return Z

@app.route("/")
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ALU Simulator - Stepwise Input</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                margin: 20px;
            }
            table {
                margin: 20px auto;
                border-collapse: collapse;
                border: 1px solid black;
            }
            th, td {
                border: 1px solid black;
                padding: 8px;
                text-align: center;
            }
            .input-box {
                width: 50px;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <h1>ALU Simulator</h1>
        <h2>Registers</h2>
        <form id="registerForm">
            <table>
                <thead>
                    <tr>
                        <th>Register</th>
                        <th>Decimal Value</th>
                    </tr>
                </thead>
                <tbody id="registerTable">
                    <!-- Register table rows -->
                </tbody>
            </table>
            <button type="button" onclick="submitRegisters()">Update Registers</button>
        </form>
        <h2>Stepwise Instruction Input</h2>
        <form id="instructionForm">
            <table>
                <tr>
                    <td>Opcode (4 bits):</td>
                    <td>
                        <input type="text" id="opcode" class="input-box" maxlength="4" oninput="updateOpcode()" placeholder="0000">
                    </td>
                    <td><span id="opcodeDesc">Operation Description</span></td>
                </tr>
                <tr>
                    <td>Register A (4 bits):</td>
                    <td>
                        <input type="text" id="regA" class="input-box" maxlength="4" oninput="updateRegister('regA', 'A')">
                    </td>
                    <td><span id="regADesc">A = Register 0</span></td>
                </tr>
                <tr>
                    <td>Register B (4 bits):</td>
                    <td>
                        <input type="text" id="regB" class="input-box" maxlength="4" oninput="updateRegister('regB', 'B')">
                    </td>
                    <td><span id="regBDesc">B = Register 0</span></td>
                </tr>
                <tr>
                    <td>Register C (4 bits):</td>
                    <td>
                        <input type="text" id="regC" class="input-box" maxlength="4" oninput="updateRegister('regC', 'C')">
                    </td>
                    <td><span id="regCDesc">C = Register 0</span></td>
                </tr>
            </table>
            <button type="button" onclick="simulateInstruction()">Simulate Instruction</button>
        </form>
        <h3>Result</h3>
        <p id="resultDecimal">Decimal: </p>
        <p id="resultBinary">Binary: </p>
        <h2>Registers After Instruction</h2>
        <table>
            <thead>
                <tr>
                    <th>Register</th>
                    <th>Value (Binary)</th>
                </tr>
            </thead>
            <tbody id="updatedRegisterTable"></tbody>
        </table>
        <script>
            const OPCODE_DESCRIPTIONS = {{ descriptions|tojson }};
            function updateOpcode() {
                const opcode = document.getElementById("opcode").value.trim();
                const desc = OPCODE_DESCRIPTIONS[opcode] || "Invalid Opcode";
                document.getElementById("opcodeDesc").textContent = desc;
            }

            function updateRegister(id, type) {
                const value = document.getElementById(id).value.trim();
                if (/^[0-1]{4}$/.test(value)) {
                    const registerIndex = parseInt(value, 2); // Convert binary to integer
                    document.getElementById(`${type}Desc`).textContent = `${type} = Register ${registerIndex}`;
                } else {
                    document.getElementById(`${type}Desc`).textContent = "Invalid Register";
                }
            }

            async function submitRegisters() {
                const registerValues = [];
                document.querySelectorAll(".register-input").forEach((input, index) => {
                    const value = parseInt(input.value, 10) || 0;
                    registerValues.push(value);
                });

                const response = await fetch("/update_registers", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ registers: registerValues }),
                });

                const data = await response.json();
                if (data.error) {
                    alert(data.error);
                } else {
                    updateRegisterTable(data.registers);
                }
            }

            async function simulateInstruction() {
                const opcode = document.getElementById("opcode").value.trim();
                const regA = document.getElementById("regA").value.trim();
                const regB = document.getElementById("regB").value.trim();
                const regC = document.getElementById("regC").value.trim();

                if (![opcode, regA, regB, regC].every(val => /^[01]{4}$/.test(val))) {
                    alert("Please enter valid 4-bit binary inputs for all fields.");
                    return;
                }

                const response = await fetch("/simulate_instruction", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        opcode: parseInt(opcode, 2),
                        regA: parseInt(regA, 2),
                        regB: parseInt(regB, 2),
                        regC: parseInt(regC, 2),
                    }),
                });

                const data = await response.json();
                if (data.error) {
                    alert(data.error);
                } else {
                    document.getElementById("resultDecimal").textContent = `Decimal: ${data.resultDecimal}`;
                    document.getElementById("resultBinary").textContent = `Binary: ${data.resultBinary}`;
                    updateRegisterTable(data.registers);
                }
            }

            function updateRegisterTable(registers) {
                const table = document.getElementById("updatedRegisterTable");
                table.innerHTML = "";
                registers.forEach((reg, index) => {
                    table.innerHTML += `<tr><td>R${index}</td><td>${reg.toString(2).padStart(16, "0")}</td></tr>`;
                });
            }

            function loadRegisters() {
                const table = document.getElementById("registerTable");
                table.innerHTML = "";
                for (let i = 0; i < 16; i++) {
                    table.innerHTML += `
                        <tr>
                            <td>R${i}</td>
                            <td><input type="number" class="register-input" value="0" min="0" max="65535"></td>
                        </tr>
                    `;
                }
            }

            window.onload = loadRegisters;
        </script>
    </body>
    </html>
    """, descriptions=OPCODE_DESCRIPTIONS)

@app.route("/update_registers", methods=["POST"])
def update_registers():
    global registers
    data = request.json
    new_registers = data.get("registers")
    if not new_registers or len(new_registers) != 16:
        return jsonify({"error": "Invalid register data."}), 400
    registers = [int(val) for val in new_registers]
    return jsonify({"message": "Registers updated.", "registers": registers})

@app.route("/simulate_instruction", methods=["POST"])
def simulate_instruction():
    data = request.json
    opcode = data.get("opcode")
    regA = data.get("regA")
    regB = data.get("regB")
    regC = data.get("regC")

    if any(val is None or val < 0 or val > 15 for val in [opcode, regA, regB, regC]):
        return jsonify({"error": "Invalid instruction components."}), 400

    result = simulate_alu(opcode, regA, regB, regC)
    return jsonify({
        "resultDecimal": result,
        "resultBinary": f"{result:016b}",
        "registers": registers
    })

if __name__ == "__main__":
    app.run(debug=True)