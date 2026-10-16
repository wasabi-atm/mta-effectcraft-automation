// CarOnSale v3 (premium, few words): one car, bidders across Europe, SOLD.
// A) light-band reveal of their Opel, LED bar ignites, anamorphic flares
// B) the car dives into an auction card floating over Germany on a perspective dot map of Europe
// C) bids arc in from 14 cities, the price ticks up  ("More bidders. Better price." - their claim: Europe-wide buyer base, more bidders per vehicle)
// D) real extruded 3D "SOLD" (Cinema 4D renderer, nested) slams in, shockwaves roll across the map
// E) yellow wipe -> logo with a light sweep + their CTA "Register now for free"
// Look: caronsale.com/en (15 Oct): black, yellow #FFCD19, their own Opel photo.
(function () {
    var BR = "/Users/wira/Desktop/mta-instantly-campaiign/campaigns/2026-10-15_eu-sales-enablement-hiring/media/sneakpeek/_brand/caronsale.com/";
    var BG = "#000000", Y = "#FFCD19", HOT = "#FFF3C4", WHITE = "#ffffff";
    var CITY = { Paris: [516.6, 349.9], Madrid: [368.3, 560.5], Barcelona: [496.4, 533.1], Lisbon: [239.5, 611.0], Milan: [643.7, 427.7], Rome: [712.9, 519.1], Vienna: [778.2, 364.1],
        Warsaw: [851.6, 280.7], Prague: [738.7, 324.0], Amsterdam: [567.9, 277.9], Brussels: [556.3, 308.2], Budapest: [830.4, 380.0], Lyon: [558.8, 420.5], Krakow: [839.3, 324.4],
        Marseille: [566.2, 481.8], Bucharest: [981.1, 453.0], Athens: [969.8, 634.0], Zurich: [631.3, 382.9] };
    var GROUND = [658.0, 305.1], CARD = [658, 180];
    // grow a ring by its ellipse size (not layer scale) so the stroke stays thin
    var ringSize = function (l) { return l.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group").property("ADBE Vector Shape - Ellipse").property("ADBE Vector Ellipse Size"); };

    // ---------- nested 3D SOLD (real extrusion needs the Cinema 4D renderer) ----------
    var sc = MTA.newComp("SOLD3D_caronsale", BG, 2.4);
    sc.renderer = "ADBE Ernst";
    var st = MTA.text(sc, { text: "SOLD", font: MTA.F.black, size: 250, color: Y, just: "C", tracking: 20, center: true, pos: [640, 360] });
    st.threeDLayer = true;
    var ex = st.property("ADBE Extrsn Options Group");
    ex.property("ADBE Extrsn Depth").setValue(70);
    ex.property("ADBE Bevel Styles").setValue(2); ex.property("ADBE Bevel Depth").setValue(7);
    var TG = st.property("ADBE Transform Group");
    MTA.k(TG.property("ADBE Position"), [[0, [640, 360, -1500]], [0.22, [640, 360, 40]], [0.32, [640, 360, 0]]], "out");
    MTA.k(TG.property("ADBE Rotate Y"), [[0, 95], [0.22, -10], [0.36, 4], [0.48, 0]], "out");
    MTA.k(TG.property("ADBE Rotate X"), [[0, -35], [0.22, 6], [0.4, 0]], "out");
    MTA.k(TG.property("ADBE Rotate Z"), [[0, -20], [0.26, -6]], "out");
    var key = sc.layers.addLight("key", [640, 360]); key.lightType = LightType.POINT;
    key.property("ADBE Light Options Group").property("ADBE Light Intensity").setValue(150);
    key.property("ADBE Transform Group").property("ADBE Position").setValue([250, 60, -700]);
    var rim = sc.layers.addLight("rim", [640, 360]); rim.lightType = LightType.POINT;
    rim.property("ADBE Light Options Group").property("ADBE Light Intensity").setValue(90);
    rim.property("ADBE Light Options Group").property("ADBE Light Color").setValue(MTA.hex("#FF8A00"));
    rim.property("ADBE Transform Group").property("ADBE Position").setValue([1150, 650, -300]);
    var amb = sc.layers.addLight("amb", [640, 360]); amb.lightType = LightType.AMBIENT;
    amb.property("ADBE Light Options Group").property("ADBE Light Intensity").setValue(38);

    // ---------- main comp ----------
    var c = MTA.newComp("SP_caronsale", BG);
    MTA.solid(c, BG, "bg");
    var RIG = MTA.camRig(c), R = [];

    // B/C) the map (static plate, appears at the dive)
    var map = MTA.image(c, BR + "europe.png", 1280, [640, 360]); map.inPoint = 1.18;
    var ms0 = MTA.P(map, "scale").value[0];
    MTA.k(MTA.P(map, "scale"), [[1.18, [ms0 * 1.25, ms0 * 1.25]], [1.5, [ms0, ms0]]], "out");
    MTA.k(MTA.P(map, "op"), [[1.18, 0], [1.4, 100]], "lin");
    R.push(map);
    var glowG = MTA.glowBlob(c, "#5a4300", GROUND, 260, 100); glowG.inPoint = 1.35;
    MTA.k(MTA.P(glowG, "op"), [[1.35, 0], [1.6, 100]], "lin");
    R.push(glowG);

    // C) bids: comet arcs from cities to Germany, origin + arrival pulses, price ticks
    var order = ["Paris", "Milan", "Madrid", "Warsaw", "Vienna", "Amsterdam", "Rome", "Lyon", "Budapest", "Barcelona", "Brussels", "Krakow", "Lisbon", "Bucharest"];
    var prices = [17900, 18250, 18600, 18900, 19300, 19650, 19900, 20250, 20500, 20800, 21050, 21200, 21350, 21480];
    var arrive = [];
    for (var i = 0; i < order.length; i++) {
        var S = CITY[order[i]], E = GROUND, tl = 1.55 + i * 0.075, TR = 0.34;
        var dx = E[0] - S[0], dy = E[1] - S[1], dist = Math.sqrt(dx * dx + dy * dy), lift = 50 + dist * 0.42;
        var C1 = [S[0] + dx * 0.25, S[1] + dy * 0.25 - lift], C2 = [S[0] + dx * 0.75, S[1] + dy * 0.75 - lift];
        var arc = MTA.path(c, { name: "bid " + order[i], pts: [S, E], outT: [[C1[0] - S[0], C1[1] - S[1]], [0, 0]], inT: [[0, 0], [C2[0] - E[0], C2[1] - E[1]]], stroke: Y, sw: 4, pos: [0, 0], trim: true });
        var tr = arc.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group").property("ADBE Vector Filter - Trim");
        MTA.k(tr.property("ADBE Vector Trim End"), [[tl, 0], [tl + TR, 100]], "inout");
        MTA.k(tr.property("ADBE Vector Trim Start"), [[tl + 0.1, 0], [tl + TR + 0.12, 100]], "inout");
        MTA.glow(arc, 22, 1.6);
        arc.inPoint = tl; arc.outPoint = tl + TR + 0.14;
        R.push(arc);
        var od = MTA.ellipse(c, { name: "src " + i, w: 12, fill: HOT, pos: S }); od.inPoint = tl - 0.02;
        MTA.k(MTA.P(od, "scale"), [[tl - 0.02, [0, 0]], [tl + 0.06, [160, 160]], [tl + 0.2, [100, 100]]], "out");
        MTA.k(MTA.P(od, "op"), [[2.9, 100], [3.2, 60]], "lin");
        MTA.glow(od, 16, 1.2);
        var orr = MTA.ellipse(c, { name: "src ring " + i, w: 20, stroke: Y, sw: 3, pos: S }); orr.inPoint = tl;
        MTA.k(ringSize(orr), [[tl, [10, 10]], [tl + 0.35, [52, 52]]], "out");
        MTA.k(MTA.P(orr, "op"), [[tl, 100], [tl + 0.35, 0]], "lin");
        orr.outPoint = tl + 0.36;
        R.push(od, orr);
        var ta = tl + TR; arrive.push(ta);
        var gr = MTA.ellipse(c, { name: "hit " + i, w: 60, stroke: Y, sw: 4, pos: E }); gr.inPoint = ta;
        MTA.P(gr, "scale").setValue([100, 42]);
        MTA.k(ringSize(gr), [[ta, [60, 60]], [ta + 0.4, [250, 250]]], "out");
        MTA.k(MTA.P(gr, "op"), [[ta, 90], [ta + 0.4, 0]], "lin");
        gr.outPoint = ta + 0.42;
        R.push(gr);
    }

    // the auction card the car dives into (frame, pin)
    var pin = MTA.path(c, { name: "pin", pts: [[CARD[0], CARD[1] + 98], GROUND], stroke: Y, sw: 3, pos: [0, 0] }); pin.inPoint = 1.38;
    MTA.k(MTA.P(pin, "op"), [[1.38, 0], [1.48, 100]], "lin");
    var gdot = MTA.ellipse(c, { name: "ground dot", w: 18, fill: HOT, pos: GROUND }); gdot.inPoint = 1.38; MTA.P(gdot, "scale").setValue([100, 45]); MTA.glow(gdot, 20, 1.5);
    var frame = MTA.rect(c, { name: "card", w: 344, h: 198, r: 18, fill: "#0b0b0b", stroke: Y, sw: 4, pos: CARD }); frame.inPoint = 1.36;
    MTA.k(MTA.P(frame, "scale"), [[1.36, [70, 70]], [1.46, [104, 104]], [1.54, [100, 100]]], "inout");
    MTA.glow(frame, 30, 0.8);
    R.push(pin, gdot, frame);

    // A) the car: band reveal, then dives into the card
    var car = MTA.image(c, BR + "opel.png", 1280, [640, 330]);
    var cs = MTA.P(car, "scale").value[0], cardS = cs * 330 / 1280;
    var mk = car.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
    var band = function (h) { var s = new Shape(); s.vertices = [[-10, 212 - h], [1010, 212 - h], [1010, 212 + h], [-10, 212 + h]]; s.closed = true; return s; };
    var mp = mk.property("ADBE Mask Shape");
    mp.setValueAtTime(0.15, band(0)); mp.setValueAtTime(0.8, band(222)); mp.setValueAtTime(1.0, band(420));
    mk.property("ADBE Mask Feather").setValue([0, 60]);
    MTA.k(MTA.P(car, "scale"), [[1.12, [cs, cs]], [1.42, [cardS, cardS]]], "inout");
    MTA.k(MTA.P(car, "pos"), [[1.12, [640, 330]], [1.42, CARD]], "inout");
    R.push(car);
    // light edges of the opening band
    var edges = [];
    for (var e2 = 0; e2 < 2; e2++) {
        var ln = MTA.rect(c, { name: "band edge " + e2, w: 1280, h: 3, r: 0, fill: HOT, pos: [640, 244] });
        MTA.k(MTA.P(ln, "pos"), [[0.15, [640, 244]], [0.8, [640, e2 ? 528 : -40]]], "inout");
        MTA.k(MTA.P(ln, "op"), [[0.1, 0], [0.18, 100], [0.7, 100], [0.82, 0]], "lin");
        MTA.k(MTA.P(ln, "scale"), [[0.1, [0, 100]], [0.3, [100, 100]]], "out");
        MTA.glow(ln, 40, 2.2);
        ln.outPoint = 0.85; edges.push(ln);
    }
    // LED bar ignites left to right, flares at both ends
    var led = MTA.path(c, { name: "led bar", pts: [[282, 244], [1004, 244]], stroke: HOT, sw: 7, pos: [0, 0], trim: true });
    MTA.k(MTA.trimEnd(led), [[0.42, 0], [0.7, 100]], "inout");
    MTA.k(MTA.P(led, "op"), [[0.42, 100], [0.95, 100], [1.12, 0]], "lin");
    MTA.glow(led, 45, 2.4); led.outPoint = 1.14;
    var fx = [[294, 244, 0.5], [992, 244, 0.68]];
    for (var f = 0; f < 2; f++) {
        var streak = MTA.ellipse(c, { name: "flare " + f, w: 900, h: 6, fill: HOT, pos: [fx[f][0], fx[f][1]] });
        MTA.k(MTA.P(streak, "scale"), [[fx[f][2], [0, 100]], [fx[f][2] + 0.12, [100, 100]], [1.05, [60, 100]]], "out");
        MTA.k(MTA.P(streak, "op"), [[fx[f][2], 0], [fx[f][2] + 0.05, 100], [0.95, 80], [1.12, 0]], "lin");
        MTA.glow(streak, 30, 2.0); streak.outPoint = 1.14;
        var core = MTA.ellipse(c, { name: "core " + f, w: 46, fill: WHITE, pos: [fx[f][0], fx[f][1]] });
        MTA.pop(core, fx[f][2], 0.18, 100, 170);
        MTA.k(MTA.P(core, "op"), [[0.95, 100], [1.12, 0]], "lin");
        MTA.glow(core, 60, 2.6); core.outPoint = 1.14;
    }

    // the price above the card
    var price = MTA.text(c, { text: "€17,900", font: MTA.F.black, size: 66, color: Y, just: "C", center: true, pos: [CARD[0], 40] });
    price.inPoint = 1.5;
    var fmt = function (n) { return "€" + Math.floor(n / 1000) + "," + ("00" + (n % 1000)).slice(-3); };
    MTA.setText(price, 0, fmt(prices[0]));
    var sk = [[1.5, [60, 60]], [1.62, [100, 100]]];
    for (var p = 1; p < prices.length; p++) {
        MTA.setText(price, arrive[p], fmt(prices[p]));
        sk.push([arrive[p], [100, 100]], [arrive[p] + 0.03, [109, 109]], [arrive[p] + 0.07, [100, 100]]);
    }
    MTA.k(MTA.P(price, "scale"), sk, "out");
    MTA.k(MTA.P(price, "op"), [[1.5, 0], [1.58, 100]], "lin");
    MTA.shadow(price, 80, 0, 24);
    R.push(price);

    // one line, bottom, on a soft dark band
    var shadeB = MTA.solid(c, "#000000", "line band"); shadeB.inPoint = 1.7;
    var bmk = shadeB.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
    var bs = new Shape(); bs.vertices = [[-100, 600], [1380, 600], [1380, 820], [-100, 820]]; bs.closed = true;
    bmk.property("ADBE Mask Shape").setValue(bs); bmk.property("ADBE Mask Feather").setValue([0, 90]);
    MTA.k(MTA.P(shadeB, "op"), [[1.7, 0], [1.85, 85]], "lin");
    var line = MTA.text(c, { text: "More bidders. Better price.", font: MTA.F.heavy, size: 54, color: WHITE, just: "C", center: true, pos: [640, 660] });
    line.inPoint = 1.8;
    var lAnim = line.property("ADBE Text Properties").property("ADBE Text Animators").addProperty("ADBE Text Animator");
    var lProps = lAnim.property("ADBE Text Animator Properties");
    lProps.addProperty("ADBE Text Opacity").setValue(0);
    lProps.addProperty("ADBE Text Position 3D").setValue([0, 26, 0]);
    var lSel = lAnim.property("ADBE Text Selectors").addProperty("ADBE Text Selector");
    MTA.k(lSel.property("ADBE Text Percent Start"), [[1.8, 0], [2.25, 100]], "out");
    R.push(shadeB, line);

    // D) SOLD: nested 3D, impact flash, shockwaves, shake
    var sold = c.layers.add(sc); sold.startTime = 2.82; sold.inPoint = 2.82; MTA.P(sold, "pos").setValue([CARD[0], CARD[1] + 10]);
    MTA.shadow(sold, 85, 18, 30);
    var IMP = 3.04;
    for (var w = 0; w < 3; w++) {
        var wave = MTA.ellipse(c, { name: "shock " + w, w: 100, stroke: w ? Y : HOT, sw: 6 - w * 2, pos: GROUND });
        wave.inPoint = IMP + w * 0.07; MTA.P(wave, "scale").setValue([100, 42]);
        MTA.k(ringSize(wave), [[IMP + w * 0.07, [100, 100]], [IMP + 0.55 + w * 0.07, [1500, 1500]]], "out");
        MTA.k(MTA.P(wave, "op"), [[IMP + w * 0.07, 100], [IMP + 0.55 + w * 0.07, 0]], "lin");
        MTA.glow(wave, 14, 1.2);
        wave.outPoint = IMP + 0.6 + w * 0.07;
        R.push(wave);
    }
    var flash = MTA.solid(c, HOT, "impact flash"); flash.inPoint = IMP; flash.outPoint = IMP + 0.15;
    MTA.k(MTA.P(flash, "op"), [[IMP, 16], [IMP + 0.1, 0]], "lin");
    flash.blendingMode = BlendingMode.ADD;

    MTA.attach(R, RIG);
    MTA.k(MTA.P(RIG, "pos"), [[IMP - 0.01, [0, 0]], [IMP + 0.02, [-10, 7]], [IMP + 0.05, [9, -6]], [IMP + 0.08, [-6, 4]], [IMP + 0.11, [4, -2]], [IMP + 0.15, [0, 0]]], "lin");

    // E) yellow wipe to the end card
    var wipe = MTA.rect(c, { name: "wipe", w: 1500, h: 1100, r: 0, fill: Y, pos: [-1200, 360] }); wipe.inPoint = 3.45; wipe.outPoint = 3.85;
    MTA.P(wipe, "rot").setValue(12);
    MTA.k(MTA.P(wipe, "pos"), [[3.5, [-1200, 360]], [3.66, [640, 360]], [3.82, [2500, 360]]], "inout");
    MTA.whipBlur(c, [[3.48, 3.82, 90]], 0);
    var endBg = MTA.solid(c, BG, "end bg"); endBg.inPoint = 3.66; endBg.moveAfter(wipe);
    var faint = MTA.image(c, BR + "europe.png", 1280, [640, 360]); faint.inPoint = 3.66; MTA.P(faint, "op").setValue(18); faint.moveAfter(wipe);
    var logo = MTA.image(c, BR + "logo.png", 600, [640, 300]); logo.inPoint = 3.68; logo.moveAfter(wipe);
    var ls = MTA.P(logo, "scale").value[0];
    MTA.k(MTA.P(logo, "scale"), [[3.68, [ls * 0.75, ls * 0.75]], [3.9, [ls * 1.04, ls * 1.04]], [4.05, [ls, ls]]], "out");
    var sw = logo.property("ADBE Effect Parade").addProperty("CC Light Sweep");
    try {
        sw.property("Direction").setValue(-30); sw.property("Width").setValue(70);
        sw.property("Sweep Intensity").setValue(90); sw.property("Edge Intensity").setValue(60);
        MTA.k(sw.property("Center"), [[3.95, [-250, 300]], [4.45, [1500, 300]]], "inout");
    } catch (eSw) {}
    var btn = MTA.button(c, { text: "Register now for free", bg: Y, fg: BG, radius: 6, h: 90, padX: 52, font: MTA.F.semi, size: 38, pos: [640, 468] });
    btn.inPoint = 4.15; MTA.pop(btn, 4.15, 0.3);
    for (var z = 1; z <= c.numLayers; z++) { if (c.layer(z).parent === btn) { c.layer(z).inPoint = 4.15; } }
    btn.moveAfter(wipe);
    for (var z2 = 1; z2 <= c.numLayers; z2++) { if (c.layer(z2).parent === btn) { c.layer(z2).moveBefore(btn); } }
    MTA.motionBlurAll(c);
    for (var mb = 1; mb <= c.numLayers; mb++) { var lm = c.layer(mb); if (/^shock |^hit |^src ring /.test(lm.name)) { lm.motionBlur = false; } }
})();
