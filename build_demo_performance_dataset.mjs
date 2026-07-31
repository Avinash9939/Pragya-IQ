import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "C:/Users/akkum/OneDrive/Desktop/Project/outputs/ai-performance-demo";
await fs.mkdir(outputDir, { recursive: true });

// Deterministic random generator: the demo remains reproducible on every run.
let seed = 20260716;
function random() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

const products = [
  ["Orbit Laptop", "Technology", 1800, 28, "growing"],
  ["Nova Tablet", "Technology", 1300, 20, "growing"],
  ["Pulse Headphones", "Technology", 800, 15, "growing"],
  ["Vertex Monitor", "Technology", 1500, -24, "declining"],
  ["Echo Printer", "Technology", 1100, -18, "declining"],
  ["Harbor Chair", "Furniture", 1050, 12, "growing"],
  ["Summit Desk", "Furniture", 1450, -17, "declining"],
  ["Cedar Bookcase", "Furniture", 900, 6, "stable"],
  ["Atlas Binder", "Office Supplies", 650, 3, "stable"],
  ["Lumen Paper", "Office Supplies", 720, 16, "growing"],
  ["Quill Storage", "Office Supplies", 780, -14, "declining"],
  ["Beacon Labels", "Office Supplies", 600, 9, "growing"],
];
const regions = [["West", 1.12], ["East", 1.00], ["Central", 0.88]];
const headers = [
  "Order Date", "Order ID", "Customer ID", "Customer Name", "Product ID", "Product Name", "Category", "Region",
  "Sales", "Quantity", "Profit", "Discount", "Marketing Spend", "Inventory Level", "Return Rate", "Customer Satisfaction"
];
const rows = [headers];
const start = new Date(Date.UTC(2025, 0, 6));

for (let week = 0; week < 36; week++) {
  for (let p = 0; p < products.length; p++) {
    const [product, category, base, weeklySlope] = products[p];
    for (let r = 0; r < regions.length; r++) {
      const [region, regionMultiplier] = regions[r];
      const date = new Date(start.getTime() + week * 7 * 86400000 + r * 86400000);
      const seasonal = 1 + Math.sin((week / 8) + p) * 0.07;
      const noise = 0.93 + random() * 0.14;
      const sales = Math.max(90, (base + weeklySlope * week) * regionMultiplier * seasonal * noise);
      const isDeclining = weeklySlope < 0;
      const discount = isDeclining ? 0.10 + random() * 0.08 : 0.03 + random() * 0.07;
      const returnRate = Math.max(0.01, Math.min(0.25, (isDeclining ? 0.10 : 0.045) + random() * 0.035));
      const satisfaction = Math.max(2.5, Math.min(5, (isDeclining ? 3.45 : 4.25) + (random() - 0.5) * 0.45));
      const quantity = Math.max(2, Math.round(sales / (45 + p * 8)));
      const marketing = Math.round((isDeclining ? 0.045 : 0.08) * sales + random() * 45);
      const inventory = Math.round(Math.max(12, quantity * (isDeclining ? 1.9 : 1.25) + random() * 30));
      const profit = sales * (0.27 - discount * 0.45 - returnRate * 0.20) - marketing * 0.18;
      const customerNumber = (p * 31 + r * 9 + week * 7) % 120 + 1;
      rows.push([
        date.toISOString().slice(0, 10),
        `ORD-${String(week + 1).padStart(2, "0")}-${String(p + 1).padStart(2, "0")}-${r + 1}`,
        `CUST-${String(customerNumber).padStart(3, "0")}`,
        `Customer ${String(customerNumber).padStart(3, "0")}`,
        `PRD-${String(p + 1).padStart(3, "0")}`,
        product, category, region,
        Math.round(sales * 100) / 100, quantity, Math.round(profit * 100) / 100,
        Math.round(discount * 1000) / 1000, marketing, inventory,
        Math.round(returnRate * 1000) / 1000, Math.round(satisfaction * 100) / 100,
      ]);
    }
  }
}

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("AI Performance Demo");
sheet.showGridLines = false;
sheet.getRange(`A1:P${rows.length}`).values = rows;
sheet.getRange("A1:P1").format = { fill: "#172554", font: { bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
sheet.getRange(`A2:A${rows.length}`).format.numberFormat = "yyyy-mm-dd";
sheet.getRange(`I2:I${rows.length}`).format.numberFormat = "#,##0.00";
sheet.getRange(`K2:K${rows.length}`).format.numberFormat = "#,##0.00";
sheet.getRange(`L2:L${rows.length}`).format.numberFormat = "0.0%";
sheet.getRange(`M2:N${rows.length}`).format.numberFormat = "#,##0";
sheet.getRange(`O2:O${rows.length}`).format.numberFormat = "0.0%";
sheet.getRange(`P2:P${rows.length}`).format.numberFormat = "0.00";
sheet.getRange(`A1:P${rows.length}`).format.autofitColumns();
sheet.getRange(`A1:P${rows.length}`).format.autofitRows();
sheet.getRange(`A1:P${rows.length}`).format.borders = { preset: "outside", style: "thin", color: "#CBD5E1" };
sheet.freezePanes.freezeRows(1);
sheet.tables.add(`A1:P${rows.length}`, true, "AIPerformanceDemoTable");

const notes = workbook.worksheets.add("Read Me");
notes.showGridLines = false;
notes.getRange("A1:D1").merge();
notes.getRange("A1").values = [["AI Performance Intelligence — Demo Dataset"]];
notes.getRange("A1").format = { fill: "#172554", font: { bold: true, color: "#FFFFFF", size: 16 }, horizontalAlignment: "center" };
notes.getRange("A3:B8").values = [
  ["Purpose", "Upload this workbook to test every dashboard section."],
  ["Detected date", "Order Date"],
  ["Detected entity", "Product Name"],
  ["Primary metric", "Sales"],
  ["Growing entities", "Orbit Laptop, Nova Tablet, Pulse Headphones, Harbor Chair, Lumen Paper, Beacon Labels"],
  ["Declining entities", "Vertex Monitor, Echo Printer, Summit Desk, Quill Storage"],
];
notes.getRange("A3:A8").format = { fill: "#E0E7FF", font: { bold: true, color: "#172554" } };
notes.getRange("A3:B8").format.wrapText = true;
notes.getRange("A1:D8").format.autofitColumns();

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(`${outputDir}/ai_performance_intelligence_demo.xlsx`);
console.log(`Created ${rows.length - 1} rows at ${outputDir}`);
