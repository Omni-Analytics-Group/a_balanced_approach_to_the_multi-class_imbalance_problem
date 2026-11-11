"use strict";

// Interactive site for the dissertation hub. Reads window.SITE_DATA (docs/data.js),
// which scripts/build_site_data.py generates from data/citations.csv.
// All text from the data is written with textContent, never as HTML.

(function () {
  const data = window.SITE_DATA;
  if (!data) {
    document.body.insertAdjacentText("afterbegin", "Site data failed to load. Run scripts/build_site_data.py.");
    return;
  }

  const SVG_NS = "http://www.w3.org/2000/svg";
  const works = data.citations;

  const USAGE_GROUP = {
    "Uses CBA as a metric": "Class Balance Accuracy itself",
    "Builds on CBA": "Class Balance Accuracy itself",
    "Discusses CBA": "Class Balance Accuracy itself",
    Software: "Class Balance Accuracy itself",
    "Cites it for balanced accuracy": "Balanced accuracy and macro metrics",
    "Cites it for the imbalance problem": "Imbalance background and methods",
    "Cites it for a method": "Imbalance background and methods",
    Other: "Other or not determined",
    "Not determined": "Other or not determined",
  };
  const GROUPS = [
    ["Class Balance Accuracy itself", "var(--series-1)"],
    ["Balanced accuracy and macro metrics", "var(--series-2)"],
    ["Imbalance background and methods", "var(--series-3)"],
    ["Other or not determined", "var(--neutral)"],
  ];
  const GROUP_COLOR = Object.fromEntries(GROUPS);

  // ---------- small DOM helpers ----------

  function el(tag, attrs, children) {
    const node = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([key, value]) => {
      if (key === "text") node.textContent = value;
      else if (key === "class") node.className = value;
      else node.setAttribute(key, value);
    });
    (children || []).forEach((child) => node.append(child));
    return node;
  }

  function svg(tag, attrs) {
    const node = document.createElementNS(SVG_NS, tag);
    Object.entries(attrs || {}).forEach(([key, value]) => {
      if (key === "text") node.textContent = value;
      else node.setAttribute(key, value);
    });
    return node;
  }

  function safeLink(url, text) {
    if (typeof url === "string" && /^https?:\/\//.test(url)) {
      return el("a", { href: url, text, rel: "noopener", target: "_blank" });
    }
    return el("span", { text });
  }

  function countBy(items, key) {
    const counts = new Map();
    items.forEach((item) => {
      const value = typeof key === "function" ? key(item) : item[key];
      counts.set(value, (counts.get(value) || 0) + 1);
    });
    return counts;
  }

  const percent = (value) => `${(value * 100).toFixed(1)}%`;

  // ---------- tooltip ----------

  const tooltip = document.getElementById("tooltip");

  function showTooltip(event, text) {
    tooltip.textContent = text;
    tooltip.style.opacity = "1";
    const pad = 14;
    const rect = tooltip.getBoundingClientRect();
    const point = event.touches ? event.touches[0] : event;
    let x = (point.clientX || 0) + pad;
    let y = (point.clientY || 0) + pad;
    if (x + rect.width > window.innerWidth - 8) x = window.innerWidth - rect.width - 8;
    if (y + rect.height > window.innerHeight - 8) y = (point.clientY || 0) - rect.height - pad;
    tooltip.style.left = `${Math.max(8, x)}px`;
    tooltip.style.top = `${Math.max(8, y)}px`;
  }

  function hideTooltip() {
    tooltip.style.opacity = "0";
  }

  function attachTooltip(node, text) {
    node.addEventListener("mousemove", (event) => showTooltip(event, text));
    node.addEventListener("mouseleave", hideTooltip);
    node.addEventListener("focus", () => {
      const rect = node.getBoundingClientRect();
      showTooltip({ clientX: rect.left + rect.width / 2, clientY: rect.top }, text);
    });
    node.addEventListener("blur", hideTooltip);
  }

  // ---------- metrics ----------

  function metricsFor(matrix) {
    const k = matrix.length;
    const rowTotals = matrix.map((row) => row.reduce((sum, value) => sum + value, 0));
    const columnTotals = matrix.map((_, j) => matrix.reduce((sum, row) => sum + row[j], 0));
    const total = rowTotals.reduce((sum, value) => sum + value, 0);
    const ratio = (top, bottom) => (bottom > 0 ? top / bottom : 0);
    const recall = matrix.map((row, i) => ratio(row[i], rowTotals[i]));
    const precision = matrix.map((row, i) => ratio(row[i], columnTotals[i]));
    const perClass = matrix.map((row, i) => ratio(row[i], Math.max(rowTotals[i], columnTotals[i])));
    const mean = (values) => values.reduce((sum, value) => sum + value, 0) / k;
    const f1 = recall.map((r, i) => ratio(2 * r * precision[i], r + precision[i]));
    return {
      accuracy: ratio(matrix.reduce((sum, row, i) => sum + row[i], 0), total),
      balancedAccuracy: mean(recall),
      macroPrecision: mean(precision),
      macroF1: mean(f1),
      cba: mean(perClass),
      recall,
      precision,
      perClass,
    };
  }

  // ---------- header tiles ----------

  function renderTiles() {
    const disciplines = new Set(works.map((work) => work.discipline).filter((name) => name !== "Not determined"));
    const countries = new Set(works.flatMap((work) => (work.countries ? work.countries.split(" ") : [])));
    const languages = new Set(works.map((work) => work.language));
    const usingCba = works.filter((work) => USAGE_GROUP[work.usage] === "Class Balance Accuracy itself").length;
    const tiles = [
      [data.googleScholarCount, "citations on Google Scholar"],
      [works.length, "distinct citing works traced"],
      [usingCba, "use, extend, or implement CBA"],
      [disciplines.size, "disciplines"],
      [countries.size, "countries with authors citing it"],
      [languages.size, "languages"],
    ];
    const host = document.getElementById("tiles");
    tiles.forEach(([value, label]) => {
      host.append(
        el("div", { class: "card tile" }, [el("div", { class: "value", text: String(value) }), el("div", { class: "label", text: label })])
      );
    });
    const balanced = works.filter((work) => work.usage === "Cites it for balanced accuracy").length;
    document.getElementById("impact-note").textContent =
      `Google Scholar lists ${data.googleScholarCount} citations. Merging Scholar with Semantic Scholar, OpenAlex, and an earlier reading list gives ${works.length} distinct citing works. ` +
      `${usingCba} of them use, extend, discuss, or implement Class Balance Accuracy. ${balanced} cite the dissertation for balanced accuracy, the definition the scikit-learn user guide attributes to it.`;
    const read = works.filter((work) => work.evidence === "full text" || work.evidence === "partial text").length;
    document.getElementById("explorer-note").textContent =
      `All ${works.length} works. The use label and the summary come from reading the citing passage, which was possible for ${read} works. The rest are marked "Not determined".`;
    document.getElementById("footer-note").textContent =
      `Citation data collected ${data.googleScholarDate}. Page data generated ${data.generated}. Counts change as indexes update.`;
  }

  // ---------- calculator ----------

  const CLASS_NAMES = ["A", "B", "C"];
  const PRESETS = [
    ["Model 1: everything is class A", [[2000, 0, 0], [600, 0, 0], [600, 0, 0]], "Class A has 2,000 members and B and C have 600 each. Predicting A for everything is right 62.5% of the time and useless."],
    ["Model 2: one region per class", [[1000, 500, 500], [100, 500, 0], [100, 0, 500]], "The same 62.5% accuracy as Model 1. Here every class scores 50% on the weaker of recall and precision, so CBA is 50%."],
    ["90% recall, 100 to 1 imbalance", [[90000, 5000, 5000], [50, 900, 50], [50, 50, 900]], "Every class has 90% recall, so accuracy and balanced accuracy both read 90%. Most predictions of B and C are false alarms, which only precision and CBA register."],
    ["Balanced and good", [[90, 5, 5], [5, 90, 5], [5, 5, 90]], "With balanced classes and even errors, every metric agrees."],
  ];
  let matrix = PRESETS[0][1].map((row) => row.slice());

  function renderMatrixInputs() {
    const table = document.getElementById("matrix");
    table.replaceChildren();
    const head = el("tr", {}, [el("th", { text: "" })]);
    CLASS_NAMES.forEach((name) => head.append(el("th", { text: `Predicted ${name}` })));
    table.append(head);
    matrix.forEach((row, i) => {
      const line = el("tr", {}, [el("th", { text: `True ${CLASS_NAMES[i]}` })]);
      row.forEach((value, j) => {
        const input = el("input", { type: "number", min: "0", step: "1", value: String(value), "aria-label": `True ${CLASS_NAMES[i]}, predicted ${CLASS_NAMES[j]}` });
        input.addEventListener("input", () => {
          const parsed = Number(input.value);
          const next = Number.isFinite(parsed) && parsed >= 0 ? parsed : 0;
          matrix = matrix.map((r, a) => r.map((v, b) => (a === i && b === j ? next : v)));
          document.querySelectorAll("#presets button").forEach((button) => button.setAttribute("aria-pressed", "false"));
          document.getElementById("calc-note").textContent = "";
          renderMetrics();
        });
        line.append(el("td", { class: i === j ? "diagonal" : "" }, [input]));
      });
      table.append(line);
    });
  }

  function renderMetrics() {
    const result = metricsFor(matrix);
    const bars = document.getElementById("metric-bars");
    bars.replaceChildren();
    [
      ["Accuracy", result.accuracy, false],
      ["Balanced accuracy", result.balancedAccuracy, false],
      ["Macro precision", result.macroPrecision, false],
      ["Macro F1", result.macroF1, false],
      ["Class Balance Accuracy", result.cba, true],
    ].forEach(([name, value, accent]) => {
      const fill = el("div", { class: accent ? "fill accent" : "fill" });
      fill.style.width = `${Math.max(0, Math.min(1, value)) * 100}%`;
      bars.append(el("div", { class: "name", text: name }), el("div", { class: "track" }, [fill]), el("div", { class: "number", text: percent(value) }));
    });
    const table = document.getElementById("per-class");
    table.replaceChildren();
    const head = el("tr", {});
    ["Class", "Recall", "Precision", "CBA share"].forEach((label) => head.append(el("th", { text: label })));
    table.append(el("thead", {}, [head]));
    const body = el("tbody", {});
    CLASS_NAMES.forEach((name, i) => {
      const line = el("tr", {});
      [name, percent(result.recall[i]), percent(result.precision[i]), percent(result.perClass[i])].forEach((text) => line.append(el("td", { text })));
      body.append(line);
    });
    table.append(body);
  }

  function renderCalculator() {
    const host = document.getElementById("presets");
    PRESETS.forEach(([label, preset, note], index) => {
      const button = el("button", { type: "button", text: label, "aria-pressed": index === 0 ? "true" : "false" });
      button.addEventListener("click", () => {
        matrix = preset.map((row) => row.slice());
        host.querySelectorAll("button").forEach((other) => other.setAttribute("aria-pressed", "false"));
        button.setAttribute("aria-pressed", "true");
        document.getElementById("calc-note").textContent = note;
        renderMatrixInputs();
        renderMetrics();
      });
      host.append(button);
    });
    document.getElementById("calc-note").textContent = PRESETS[0][2];
    renderMatrixInputs();
    renderMetrics();
  }

  // ---------- charts ----------

  function renderYearChart() {
    const legend = document.getElementById("year-legend");
    GROUPS.forEach(([name, color]) => {
      const swatch = el("span", { class: "swatch" });
      swatch.style.background = color;
      legend.append(el("span", {}, [swatch, document.createTextNode(name)]));
    });
    const dated = works.filter((work) => work.year);
    if (!dated.length) return;
    const firstYear = Math.min(...dated.map((work) => work.year));
    const lastYear = Math.max(...dated.map((work) => work.year));
    const years = [];
    for (let year = firstYear; year <= lastYear; year += 1) years.push(year);
    const totals = years.map((year) => {
      const inYear = dated.filter((work) => work.year === year);
      const groups = countBy(inYear, (work) => USAGE_GROUP[work.usage]);
      return { year, total: inYear.length, groups };
    });
    const width = 960;
    const height = 300;
    const margin = { top: 20, right: 10, bottom: 28, left: 30 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const maxTotal = Math.max(...totals.map((entry) => entry.total));
    const step = Math.ceil(maxTotal / 4 / 5) * 5 || 1;
    const top = Math.ceil(maxTotal / step) * step;
    const band = plotWidth / years.length;
    const barWidth = Math.min(24, band * 0.6);
    const yFor = (value) => margin.top + plotHeight - (value / top) * plotHeight;
    const chart = svg("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": "Citing works per year, stacked by use" });
    for (let tick = 0; tick <= top; tick += step) {
      chart.append(svg("line", { x1: margin.left, x2: width - margin.right, y1: yFor(tick), y2: yFor(tick), stroke: tick === 0 ? "var(--axis)" : "var(--grid)", "stroke-width": 1 }));
      chart.append(svg("text", { x: margin.left - 6, y: yFor(tick) + 4, "text-anchor": "end", text: String(tick) }));
    }
    totals.forEach((entry, index) => {
      const center = margin.left + band * index + band / 2;
      let running = 0;
      const lines = [`${entry.year}: ${entry.total} citing works`];
      const group = svg("g", { class: "mark" });
      GROUPS.forEach(([name, color]) => {
        const value = entry.groups.get(name) || 0;
        if (!value) return;
        lines.push(`${value}  ${name}`);
        const yTop = yFor(running + value);
        const barHeight = Math.max(0, yFor(running) - yTop - 2);
        group.append(svg("rect", { x: center - barWidth / 2, y: yTop, width: barWidth, height: barHeight, fill: color, rx: 2 }));
        running += value;
      });
      const hit = svg("rect", { class: "hit", x: center - band / 2, y: margin.top, width: band, height: plotHeight, fill: "transparent", tabindex: "0", role: "img", "aria-label": lines.join(". ") });
      attachTooltip(hit, lines.join("\n"));
      chart.append(hit, group);
      chart.append(svg("text", { class: "value", x: center, y: yFor(entry.total) - 6, "text-anchor": "middle", text: String(entry.total) }));
      chart.append(svg("text", { x: center, y: height - 8, "text-anchor": "middle", text: String(entry.year) }));
    });
    document.getElementById("year-chart").append(chart);
  }

  function renderBarChart(hostId, entries, colorFor, onSelect) {
    if (!entries.length) return;
    const rowHeight = 30;
    const labelWidth = 290;
    const width = 480;
    const height = entries.length * rowHeight + 6;
    const maxValue = Math.max(...entries.map(([, value]) => value));
    const plotWidth = width - labelWidth - 44;
    const chart = svg("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": "Bar chart" });
    entries.forEach(([label, value], index) => {
      const y = index * rowHeight + 4;
      const barLength = Math.max(2, (value / maxValue) * plotWidth);
      const text = `${label}: ${value} citing works`;
      const hit = svg("rect", { class: "hit", x: 0, y, width, height: rowHeight - 4, fill: "transparent", tabindex: "0", role: onSelect ? "button" : "img", "aria-label": text });
      attachTooltip(hit, onSelect ? `${text}\nSelect to filter the list` : text);
      if (onSelect) {
        hit.addEventListener("click", () => onSelect(label));
        hit.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onSelect(label);
          }
        });
      }
      const group = svg("g", { class: "mark" });
      group.append(svg("path", { d: `M${labelWidth},${y + 4} h${barLength - 4} a4,4 0 0 1 4,4 v${rowHeight - 20} a4,4 0 0 1 -4,4 h${-(barLength - 4)} z`, fill: colorFor(label) }));
      chart.append(hit, group);
      chart.append(svg("text", { class: "label", x: labelWidth - 8, y: y + 17, "text-anchor": "end", text: label }));
      chart.append(svg("text", { class: "value", x: labelWidth + barLength + 6, y: y + 17, text: String(value) }));
    });
    document.getElementById(hostId).append(chart);
  }

  function sortedCounts(key) {
    return Array.from(countBy(works, key).entries()).sort((a, b) => (a[0] === "Not determined") - (b[0] === "Not determined") || b[1] - a[1]);
  }

  // ---------- explorer ----------

  const state = { search: "", discipline: "", usage: "", valuesOnly: false, sort: "year", shown: 20 };

  function fillSelect(id, placeholder, values) {
    const select = document.getElementById(id);
    select.append(el("option", { value: "", text: placeholder }));
    values.forEach((value) => select.append(el("option", { value, text: value })));
  }

  function matches(work) {
    if (state.discipline && work.discipline !== state.discipline) return false;
    if (state.usage && work.usage !== state.usage) return false;
    if (state.valuesOnly && work.reports_cba_values !== "yes") return false;
    if (state.search) {
      const haystack = [work.title, work.english_title, work.authors, work.venue, work.domain, work.how_used].join(" ").toLowerCase();
      return state.search.toLowerCase().split(/\s+/).filter(Boolean).every((term) => haystack.includes(term));
    }
    return true;
  }

  const SORTERS = {
    year: (a, b) => (b.year || 0) - (a.year || 0) || a.title.localeCompare(b.title),
    cited: (a, b) => b.cited_by - a.cited_by || (b.year || 0) - (a.year || 0),
    title: (a, b) => a.title.localeCompare(b.title),
  };

  function workCard(work) {
    const card = el("article", { class: "work" });
    card.append(el("div", { class: "title" }, [safeLink(work.url, work.title)]));
    if (work.english_title) card.append(el("div", { class: "meta", text: work.english_title }));
    const meta = [work.authors, work.venue, work.year ? String(work.year) : "undated"].filter(Boolean).join(" · ");
    card.append(el("div", { class: "meta", text: meta }));
    if (work.how_used && work.usage !== "Not determined") card.append(el("p", { class: "how", text: work.how_used }));
    if (work.quote) card.append(el("blockquote", { text: work.quote }));
    const chips = el("div", { class: "chips" });
    chips.append(el("span", { class: USAGE_GROUP[work.usage] === "Class Balance Accuracy itself" ? "chip cba" : "chip", text: work.usage }));
    if (work.discipline !== "Not determined") chips.append(el("span", { class: "chip", text: work.discipline }));
    if (work.reports_cba_values === "yes") chips.append(el("span", { class: "chip cba", text: "Reports CBA values" }));
    if (work.language && work.language !== "English") chips.append(el("span", { class: "chip", text: work.language }));
    if (work.cited_by) chips.append(el("span", { class: "chip", text: `Cited by ${work.cited_by}` }));
    chips.append(el("span", { class: "chip", text: `Evidence: ${work.evidence}` }));
    card.append(chips);
    return card;
  }

  function renderWorks() {
    const selected = works.filter(matches).sort(SORTERS[state.sort]);
    const host = document.getElementById("works");
    host.replaceChildren(...selected.slice(0, state.shown).map(workCard));
    document.getElementById("count").textContent = `${selected.length} of ${works.length} works`;
    document.getElementById("more").hidden = selected.length <= state.shown;
  }

  function setFilter(key, value, scroll) {
    state[key] = value;
    state.shown = 20;
    document.getElementById("filter-discipline").value = state.discipline;
    document.getElementById("filter-usage").value = state.usage;
    renderWorks();
    if (scroll) document.getElementById("explorer").scrollIntoView();
  }

  function renderExplorer() {
    fillSelect("filter-discipline", "All disciplines", sortedCounts("discipline").map(([name]) => name));
    fillSelect("filter-usage", "All uses", data.usageOrder.filter((name) => works.some((work) => work.usage === name)));
    document.getElementById("search").addEventListener("input", (event) => setFilter("search", event.target.value));
    document.getElementById("filter-discipline").addEventListener("change", (event) => setFilter("discipline", event.target.value));
    document.getElementById("filter-usage").addEventListener("change", (event) => setFilter("usage", event.target.value));
    document.getElementById("filter-values").addEventListener("change", (event) => setFilter("valuesOnly", event.target.checked));
    document.getElementById("sort").addEventListener("change", (event) => setFilter("sort", event.target.value));
    document.getElementById("more").addEventListener("click", () => {
      state.shown += 20;
      renderWorks();
    });
    document.getElementById("reset").addEventListener("click", () => {
      Object.assign(state, { search: "", discipline: "", usage: "", valuesOnly: false, sort: "year", shown: 20 });
      document.getElementById("search").value = "";
      document.getElementById("filter-values").checked = false;
      document.getElementById("sort").value = "year";
      setFilter("discipline", "");
    });
    renderWorks();
  }

  // ---------- resources ----------

  function renderResources() {
    const implementations = document.getElementById("implementations");
    data.implementations.forEach((item) => {
      implementations.append(el("li", {}, [safeLink(item.url, item.name), el("div", { class: "aside", text: item.notes })]));
    });
    const software = document.getElementById("software");
    data.software.forEach((item) => {
      software.append(el("li", {}, [safeLink(item.url, item.name), document.createTextNode(` (${item.language})`), el("div", { class: "aside", text: item.what })]));
    });
    const reading = document.getElementById("reading");
    const themes = new Map();
    data.reading.forEach((item) => {
      if (!themes.has(item.theme)) themes.set(item.theme, []);
      themes.get(item.theme).push(item);
    });
    themes.forEach((items, theme) => {
      const details = el("details", {}, [el("summary", { text: `${theme.charAt(0).toUpperCase()}${theme.slice(1)} (${items.length})` })]);
      const list = el("ul", { class: "resource-list" });
      items
        .sort((a, b) => a.year - b.year)
        .forEach((item) => {
          list.append(el("li", {}, [safeLink(item.url, item.title), el("div", { class: "aside", text: `${item.authors} ${item.year}. ${item.venue}. ${item.one_line}` })]));
        });
      details.append(list);
      reading.append(details);
    });
  }

  function wireCopy() {
    const button = document.getElementById("copy-bibtex");
    button.addEventListener("click", async () => {
      const text = document.getElementById("bibtex").textContent;
      try {
        await navigator.clipboard.writeText(text);
        button.textContent = "Copied";
      } catch (error) {
        button.textContent = "Select the text above to copy";
      }
      setTimeout(() => {
        button.textContent = "Copy BibTeX";
      }, 2500);
    });
  }

  renderTiles();
  renderCalculator();
  renderYearChart();
  renderBarChart("discipline-chart", sortedCounts("discipline"), () => "var(--series-1)", (label) => setFilter("discipline", label, true));
  renderBarChart("usage-chart", sortedCounts("usage"), (label) => GROUP_COLOR[USAGE_GROUP[label]], (label) => setFilter("usage", label, true));
  renderExplorer();
  renderResources();
  wireCopy();
})();
