// {{SLUG}} sneak peek. One cinematic hero moment built on the company's own story, few words,
// their own lines and their own CTA. Describe the beats here (A, B, C... with times) before building.
// Runs in EffectCraft with lib_mta.jsx loaded; MTA.ROOT / MTA.BRAND / MTA.OUT3D / MTA.COMP are set.
(function () {
    var BG = "#000000", INK = "#ffffff", ACCENT = "#2997FF";
    var c = MTA.newComp(MTA.COMP, BG);            // must be MTA.COMP ({{COMP}}): the runner renders it
    MTA.solid(c, BG, "bg");

    // a Blender pass, if 3d/hero.py rendered one:
    var HERO = MTA.OUT3D + "hero/f_0001.png";
    if (new File(HERO).exists) { var hero = MTA.sequence(c, HERO, MTA.W); hero.outPoint = 3.8; }

    var line = MTA.text(c, { text: "Their own line.", font: MTA.F.semi, size: 72, color: INK, just: "C", center: true, pos: [640, 120] });
    line.inPoint = 0.3; MTA.reveal(line, 0.3, 0.7, 22);

    // end card: logo (MTA.image(c, MTA.BRAND + "logo.png", 360, [640, 230])), their H1, their CTA
    var btn = MTA.button(c, { text: "Their CTA", bg: ACCENT, fg: "#ffffff", radius: 35, h: 70, padX: 36, font: MTA.F.semi, size: 29, pos: [640, 440] });
    btn.inPoint = 4.2; MTA.pop(btn, 4.2, 0.3);
    for (var z = 1; z <= c.numLayers; z++) { if (c.layer(z).parent === btn) { c.layer(z).inPoint = 4.2; } }
    MTA.motionBlurAll(c);
})();
