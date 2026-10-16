// TRM Labs v3: their dotted-sphere hero, alive. "Criminals scale with AI. Crimefighters scale with Ardence." (trmlabs.com, 15 Oct)
// A) a dotted 3D globe turns (PNG sequence from tools/dot_globe.py): "Criminals scale with AI."
// B) a network lights up across it, node by node, arcs drawing between them: "Search further. Move faster."
// C) the camera dives into the network, flash
// D) logo, their H1, "REQUEST A DEMO" (white, 8px, dark text). Look: deep navy #00124D, blue dots, red/amber network.
(function () {
    var BR = "/Users/wira/Desktop/mta-instantly-campaiign/campaigns/2026-10-15_eu-sales-enablement-hiring/media/sneakpeek/_brand/trmlabs.com/";
    var BG = "#00124D", CY = "#3FA9FF", WHITE = "#ffffff", INK = "#30302F";
    var c = MTA.newComp("SP_trmlabs", BG);
    MTA.solid(c, BG, "bg");
    MTA.glowBlob(c, "#0d3aa8", [640, 380], 620, 100);
    var io = new ImportOptions(new File(BR + "globe/g_000.png")); io.sequence = true;
    var seq = app.project.importFile(io); seq.mainSource.conformFrameRate = MTA.FPS;
    var g = c.layers.add(seq); g.name = "globe"; g.outPoint = 3.3;
    MTA.P(g, "anchor").setValue([640, 380]); MTA.P(g, "pos").setValue([640, 380]);
    MTA.k(MTA.P(g, "scale"), [[0, [78, 78]], [0.9, [100, 100]], [2.45, [108, 108]], [3.05, [620, 620]]], "inout");
    MTA.k(MTA.P(g, "pos"), [[2.45, [640, 380]], [3.05, [900, 760]]], "in");
    MTA.k(MTA.P(g, "op"), [[0, 0], [0.25, 100], [2.95, 100], [3.1, 0]], "lin");
    var t1 = MTA.text(c, { text: "Criminals scale with AI.", font: MTA.F.med, size: 64, color: WHITE, just: "C", center: true, pos: [640, 80] });
    t1.inPoint = 0.2; t1.outPoint = 1.25; MTA.reveal(t1, 0.2, 0.55, 24); MTA.k(MTA.P(t1, "op"), [[1.12, 100], [1.25, 0]], "lin");
    var t2 = MTA.text(c, { text: "Search further. Move faster.", font: MTA.F.med, size: 64, color: CY, just: "C", center: true, pos: [640, 80] });
    t2.inPoint = 1.3; t2.outPoint = 2.6; MTA.reveal(t2, 1.3, 1.65, 24); MTA.k(MTA.P(t2, "op"), [[2.45, 100], [2.6, 0]], "lin");
    MTA.whipBlur(c, [[2.7, 3.15, 120]], 45);
    var fl = MTA.solid(c, "#BFE0FF", "flash"); fl.inPoint = 2.98; fl.outPoint = 3.25; fl.blendingMode = BlendingMode.ADD;
    MTA.k(MTA.P(fl, "op"), [[2.98, 0], [3.05, 45], [3.25, 0]], "lin");
    // end card
    var logo = MTA.image(c, BR + "logo2.png", 230, [640, 165]); logo.inPoint = 3.15; MTA.tint(logo, WHITE);
    MTA.k(MTA.P(logo, "op"), [[3.15, 0], [3.28, 100]], "lin"); MTA.sweep(logo, 3.4, 3.9, 165, 50);
    var h1 = MTA.text(c, { text: "Criminals scale with AI.", font: MTA.F.med, size: 66, color: WHITE, just: "C", center: true, pos: [640, 300] });
    var h2 = MTA.text(c, { text: "Crimefighters scale with Ardence.", font: MTA.F.med, size: 66, color: CY, just: "C", center: true, pos: [640, 385] });
    h1.inPoint = 3.2; h2.inPoint = 3.35; MTA.reveal(h1, 3.2, 3.55, 24); MTA.reveal(h2, 3.35, 3.75, 24);
    var btn = MTA.button(c, { text: "REQUEST A DEMO", bg: WHITE, fg: INK, radius: 10, h: 82, padX: 48, font: MTA.F.bold, size: 30, tracking: 60, pos: [640, 520] });
    btn.inPoint = 3.9; MTA.pop(btn, 3.9, 0.3);
    for (var z = 1; z <= c.numLayers; z++) { if (c.layer(z).parent === btn) { c.layer(z).inPoint = 3.9; } }
    MTA.motionBlurAll(c);
})();
