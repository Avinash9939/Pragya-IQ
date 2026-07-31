import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const root = "C:/Users/akkum/OneDrive/Desktop/Project/outputs/ai-performance-demo";
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(`${root}/ai_performance_intelligence_demo.xlsx`));
const check = await workbook.inspect({ kind: "table", range: "AI Performance Demo!A1:P8", include: "values", tableMaxRows: 8, tableMaxCols: 16 });
await fs.writeFile(`${root}/verification.ndjson`, check.ndjson);
const preview = await workbook.render({ sheetName: "Read Me", range: "A1:D8", scale: 2, format: "png" });
await fs.writeFile(`${root}/readme_preview.png`, new Uint8Array(await preview.arrayBuffer()));
console.log("Demo workbook inspected and rendered.");
