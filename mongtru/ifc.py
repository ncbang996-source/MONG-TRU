"""Xuất mô hình IFC4 (Reference View) của móng: bê tông móng (IfcFooting), bê tông lót (IfcSlab), cốt thép
(IfcReinforcingBar - thanh tròn quét theo đường tim đã bo cung uốn), bu lông neo (IfcMechanicalFastener), lưới trục
(IfcGrid), vật liệu, màu, lớp, khối lượng. Ghi thẳng file STEP (không cần thư viện IFC). Đơn vị dài mm; cao độ: mặt
đất tự nhiên = 0 (móng 2 loại: theo cao độ thiết kế). Hình học lấy từ mô hình 3D của chương trình (view3d.Scene)."""
from __future__ import annotations

import math
import time
import uuid

from . import __version__, _meta, cad, model
from .geom import Geo
from .view3d import COL, Scene

_B64 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$"
_NS = uuid.UUID("6f1d2c1e-5b8a-4c39-9a52-3f1e0b7c9d21")
QUAD = {1: (-1, 1), 2: (1, 1), 3: (-1, -1), 4: (1, -1)}          # vị trí trụ 1..4 (trái trên, phải trên, ...)
# loại thép theo màu trong mô hình 3D: (tên, PredefinedType)
BAR_KIND = {
    "slab_x": ("Thép bản đế phương X", "MAIN"), "slab_y": ("Thép bản đế phương Y", "MAIN"),
    "chair": ("Thanh chống", "NOTDEFINED"), "pier": ("Thép chủ cổ móng", "MAIN"),
    "hoop": ("Đai cổ móng", "LIGATURE"), "tie": ("Đai phụ cổ móng", "LIGATURE"),
    "mesh": ("Lưới thép đầu trụ", "MAIN"),
}
_KIND_OF = {v: k for k, v in COL.items()}


def guid(name: str) -> str:
    """GlobalId IFC (22 ký tự) - cố định theo tên (xuất lại cùng móng cho cùng mã)."""
    n = uuid.uuid5(_NS, name).int
    return _B64[n >> 126] + "".join(_B64[(n >> (6 * i)) & 63] for i in range(20, -1, -1))


def s_(t) -> str:
    """Chuỗi STEP: ký tự ngoài ASCII -> \\X2\\HHHH\\X0\\."""
    if t is None:
        return "$"
    out = []
    for ch in str(t):
        if ch == "'":
            out.append("''")
        elif ch == "\\":
            out.append("\\\\")
        elif 32 <= ord(ch) < 127:
            out.append(ch)
        else:
            out.append("\\X2\\" + "".join(f"{b:02X}" for b in ch.encode("utf-16-be")) + "\\X0\\")
    return "'" + "".join(out) + "'"


def f_(v) -> str:
    r = f"{float(v):.6f}".rstrip("0")
    return r + "0" if r.endswith(".") else r


class _W:
    def __init__(self):
        self.rows = []

    def __call__(self, s):
        self.rows.append(s)
        return f"#{len(self.rows)}"


def _mesh(faces, scale, dz):
    """Mặt (m) -> (danh sách điểm mm, chỉ số mặt 1..n) gộp điểm trùng; kín (mỗi cạnh dùng 2 lần)?"""
    pts, idx, out = [], {}, []
    for f in faces:
        q = []
        for x, y, z in f:
            k = (round(x * scale, 2), round(y * scale, 2), round((z + dz) * scale, 2))
            if k not in idx:
                idx[k] = len(pts) + 1
                pts.append(k)
            if not q or q[-1] != idx[k]:
                q.append(idx[k])
        if len(q) > 2 and q[0] == q[-1]:
            q.pop()
        if len(q) >= 3:
            out.append(q)
    edges = {}
    for q in out:
        for a, b in zip(q, q[1:] + q[:1]):
            e = (min(a, b), max(a, b))
            edges[e] = edges.get(e, 0) + 1
    return pts, out, all(c == 2 for c in edges.values())


def _plen(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def _parts(data):
    """[(trụ q, tên loại, tham số p, scene, dz)] cho 4 trụ giống nhau (p) hoặc móng 2 loại (mp)."""
    if "TYPES" in data:
        from .lech import model as lm
        from .lech.view3d import MixedScene
        sc = MixedScene(data)
        out = []
        for i, t in enumerate(data["TYPES"]):
            for q in t["POS"]:
                out.append((q, f"{t['NAME']}", lm.type_params(data, i)))
        return out, sc, sc.z0
    p = data
    sc = Scene(Geo(p))
    return [(q, model.type_name(p), p) for q in (1, 2, 3, 4)], sc, -float(p["H1"])


def export(data: dict, path: str):
    """Ghi file IFC4. data: thông số 4 trụ giống nhau (p) hoặc móng 2 loại (mp, có khoá TYPES)."""
    if not _meta.check(cad._SIG):
        raise RuntimeError("Tệp chương trình đã bị thay đổi.")
    parts, sc, z0 = _parts(data)
    p0 = parts[0][2]
    S = 1000.0                                                   # m -> mm
    key = f"{data.get('MABV', '')}|{data.get('COT', '')}|{model.type_name(p0) if 'TYPES' not in data else data.get('TENMONG', '')}"
    G = lambda nm: guid(key + "|" + nm)
    w = _W()
    now = int(time.time())
    person = w("IFCPERSON($,$,'',$,$,$,$,$)")
    org = w(f"IFCORGANIZATION($,{s_('VE_MONGTRU')},$,$,$)")
    po = w(f"IFCPERSONANDORGANIZATION({person},{org},$)")
    app = w(f"IFCAPPLICATION({org},'{__version__}',{s_('VE_MONGTRU - Vẽ móng trụ')},'VE_MONGTRU')")
    oh = w(f"IFCOWNERHISTORY({po},{app},$,.NOCHANGE.,$,$,$,{now})")
    u_len = w("IFCSIUNIT(*,.LENGTHUNIT.,.MILLI.,.METRE.)")
    u_area = w("IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.)")
    u_vol = w("IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.)")
    u_ang = w("IFCSIUNIT(*,.PLANEANGLEUNIT.,$,.RADIAN.)")
    u_mass = w("IFCSIUNIT(*,.MASSUNIT.,.KILO.,.GRAM.)")
    units = w(f"IFCUNITASSIGNMENT(({u_len},{u_area},{u_vol},{u_ang},{u_mass}))")
    o3 = w("IFCCARTESIANPOINT((0.,0.,0.))")
    ax0 = w(f"IFCAXIS2PLACEMENT3D({o3},$,$)")
    north = w("IFCDIRECTION((0.,1.))")
    ctx = w(f"IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,{ax0},{north})")
    c_body = w(f"IFCGEOMETRICREPRESENTATIONSUBCONTEXT('Body','Model',*,*,*,*,{ctx},$,.MODEL_VIEW.,$)")
    c_foot = w(f"IFCGEOMETRICREPRESENTATIONSUBCONTEXT('FootPrint','Model',*,*,*,*,{ctx},$,.MODEL_VIEW.,$)")
    pname = f"MÓNG {data.get('TENMONG') or model.type_name(p0)} - CỘT {model.HT_NAMES[int(data.get('HT', 0))]} " \
            f"{data.get('COT', '')}".strip()
    proj = w(f"IFCPROJECT('{G('project')}',{oh},{s_(pname)},$,$,$,{s_(data.get('GD', ''))},({ctx}),{units})")
    pl_site = w(f"IFCLOCALPLACEMENT($,{ax0})")
    site = w(f"IFCSITE('{G('site')}',{oh},'Site',$,$,{pl_site},$,$,.ELEMENT.,$,$,0.,$,$)")
    pl_bld = w(f"IFCLOCALPLACEMENT({pl_site},{ax0})")
    bld = w(f"IFCBUILDING('{G('building')}',{oh},{s_('Móng trụ')},$,$,{pl_bld},$,$,.ELEMENT.,$,$,$)")
    pl_st = w(f"IFCLOCALPLACEMENT({pl_bld},{ax0})")
    st = w(f"IFCBUILDINGSTOREY('{G('storey')}',{oh},{s_('Móng')},$,$,{pl_st},$,$,.ELEMENT.,0.)")
    w(f"IFCRELAGGREGATES('{G('agg1')}',{oh},$,$,{proj},({site}))")
    w(f"IFCRELAGGREGATES('{G('agg2')}',{oh},$,$,{site},({bld}))")
    w(f"IFCRELAGGREGATES('{G('agg3')}',{oh},$,$,{bld},({st}))")

    styles = {}

    def style(name, rgb, transp=0.0, spec=64.0):
        if name not in styles:
            c = w(f"IFCCOLOURRGB($,{f_(rgb[0] / 255)},{f_(rgb[1] / 255)},{f_(rgb[2] / 255)})")
            r = w(f"IFCSURFACESTYLERENDERING({c},{f_(transp)},$,$,$,$,IFCNORMALISEDRATIOMEASURE(0.5),"
                  f"IFCSPECULAREXPONENT({f_(spec)}),.NOTDEFINED.)")
            styles[name] = w(f"IFCSURFACESTYLE({s_(name)},.BOTH.,({r}))")
        return styles[name]

    mats = {}

    def material(name, cat):
        if name not in mats:
            mats[name] = (w(f"IFCMATERIAL({s_(name)},$,{s_(cat)})"), [])
        return mats[name]

    def pset(obj, nm, props, tag):
        ps = []
        for k, v in props:
            if isinstance(v, str):
                val = f"IFCLABEL({s_(v)})"
            elif isinstance(v, bool):
                val = f"IFCBOOLEAN(.{'T' if v else 'F'}.)"
            elif isinstance(v, int):
                val = f"IFCINTEGER({v})"
            else:
                val = f"IFCREAL({f_(v)})"
            ps.append(w(f"IFCPROPERTYSINGLEVALUE({s_(k)},$,{val},$)"))
        pr = w(f"IFCPROPERTYSET('{G(tag + '|ps|' + nm)}',{oh},{s_(nm)},$,({','.join(ps)}))")
        w(f"IFCRELDEFINESBYPROPERTIES('{G(tag + '|rp|' + nm)}',{oh},$,$,({obj}),{pr})")

    def qto(obj, nm, items, tag):
        qs = []
        for k, kind, v in items:
            qs.append(w(f"IFCQUANTITY{kind}({s_(k)},$,$,{f_(v)},$)"))
        q = w(f"IFCELEMENTQUANTITY('{G(tag + '|q')}',{oh},{s_(nm)},$,$,({','.join(qs)}))")
        w(f"IFCRELDEFINESBYPROPERTIES('{G(tag + '|rq')}',{oh},$,$,({obj}),{q})")

    def faceset(faces, sty):
        pts, fs, closed = _mesh(faces, S, z0)
        pl = w("IFCCARTESIANPOINTLIST3D((" + ",".join(f"({f_(x)},{f_(y)},{f_(z)})" for x, y, z in pts) + "))")
        fx = [w("IFCINDEXEDPOLYGONALFACE((" + ",".join(str(i) for i in q) + "))") for q in fs]
        it = w(f"IFCPOLYGONALFACESET({pl},{'.T.' if closed else '.F.'},({','.join(fx)}),$)")
        w(f"IFCSTYLEDITEM({it},({sty}),$)")
        return it

    elems, layers = [], {"S-FOOTING": [], "S-REBAR": [], "S-GRID": []}
    s_bt = style(f"Bê tông {data.get('BTM', '')}".strip(), (150, 150, 150))
    s_lot = style(f"Bê tông lót {data.get('BTL', '')}".strip(), (192, 192, 192))
    s_st = style("Thép", (200, 60, 50), spec=128.0)
    s_bolt = style("Bu lông", (70, 70, 70), spec=128.0)
    m_bt = material(f"Bê tông {data.get('BTM', '')}".strip(), "Concrete")
    m_lot = material(f"Bê tông lót {data.get('BTL', '')}".strip(), "Concrete")
    m_st = material("Thép cốt bê tông", "Steel")
    m_bolt = material("Thép bu lông neo", "Steel")

    def element(cls, tag, name, items, rtype, lay, mat, extra):
        rep = w(f"IFCSHAPEREPRESENTATION({c_body},'Body','{rtype}',({','.join(items)}))")
        layers[lay].append(rep)
        shp = w(f"IFCPRODUCTDEFINITIONSHAPE($,$,({rep}))")
        pl = w(f"IFCLOCALPLACEMENT({pl_st},{ax0})")
        e = w(f"{cls}('{G(tag)}',{oh},{s_(name)},$,$,{pl},{shp},{s_(tag)},{extra})")
        elems.append(e)
        mat[1].append(e)
        return e

    for q, tname, p in parts:
        pk = QUAD[q]
        for kind, k, faces in sc.solids:
            if k != pk:
                continue
            if kind == "mong":
                e = element("IFCFOOTING", f"M{q}", f"Móng trụ {q} - {tname}", [faceset(faces, s_bt)],
                            "Tessellation", "S-FOOTING", m_bt, ".PAD_FOOTING.")
                v = model.vol_pad(p) + model.vol_col(p)
                qto(e, "Qto_FootingBaseQuantities", [("NetVolume", "VOLUME", v), ("GrossVolume", "VOLUME", v)], f"M{q}")
                pset(e, "Pset_FootingCommon", [("Reference", tname), ("LoadBearing", True)], f"M{q}")
            else:
                e = element("IFCSLAB", f"L{q}", f"Bê tông lót trụ {q}", [faceset(faces, s_lot)], "Tessellation",
                            "S-FOOTING", m_lot, ".BASESLAB.")
                a = (p["B"] + 2 * model.ML) ** 2
                qto(e, "Qto_SlabBaseQuantities", [("NetArea", "AREA", a), ("NetVolume", "VOLUME", a * model.TL)],
                    f"L{q}")
        # cốt thép theo loại + đường kính; bu lông neo
        grp = {}
        for lay, col, d, pts, closed, k in sc.bars:
            if k != pk:
                continue
            kind = _KIND_OF.get(col, "")
            if len(pts) > 2 and math.dist(pts[0], pts[-1]) < 1e-6:
                # vòng kín (đai, đai ốc): chừa chỗ nối 1Ø (thanh quét không khép trùng điểm đầu)
                a, b = pts[-2], pts[-1]
                L_ = math.dist(a, b)
                t = max(0.0, 1.0 - d / L_) if L_ > 1e-9 else 1.0
                pts = pts[:-1] + [tuple(a[i] + t * (b[i] - a[i]) for i in range(3))]
            dk = 0.0 if kind == "bolt" else round(d * 1000, 1)        # bu lông: thân + đai ốc 1 phần tử
            grp.setdefault((kind, dk), []).append((pts, d))
        for (kind, dm), bars in sorted(grp.items()):
            items = []
            for pts, d in bars:
                pl = w("IFCCARTESIANPOINTLIST3D((" + ",".join(
                    f"({f_(x * S)},{f_(y * S)},{f_((z + z0) * S)})" for x, y, z in pts) + "))")
                cv = w(f"IFCINDEXEDPOLYCURVE({pl},$,.F.)")
                it = w(f"IFCSWEPTDISKSOLID({cv},{f_(d * S / 2)},$,$,$)")
                w(f"IFCSTYLEDITEM({it},({s_bolt if kind == 'bolt' else s_st}),$)")
                items.append(it)
            tot = sum(_plen(b) for b, _ in bars)
            if kind == "bolt":
                element("IFCMECHANICALFASTENER", f"B{q}", f"Bu lông neo {data.get('BLN', '')} trụ {q}", items,
                        "AdvancedSweptSolid", "S-REBAR", m_bolt,
                        f"{f_(model.bolt_dia(p))},{f_(model.bolt_h(p) * S)},.ANCHORBOLT.")
                continue
            name, pre = BAR_KIND.get(kind, ("Cốt thép", "NOTDEFINED"))
            tag = f"R{q}-{kind}-{dm:g}"
            kg = tot * math.pi * (dm / 2000) ** 2 * 7850
            e = element("IFCREINFORCINGBAR", tag, f"{name} Ø{dm:g} trụ {q}", items, "AdvancedSweptSolid", "S-REBAR",
                        m_st, f"$,{f_(dm)},{f_(math.pi * (dm / 2000) ** 2)},{f_(tot / len(bars) * S)},.{pre}.,.TEXTURED.")
            pset(e, "Pset_ReinforcingBarCommon", [("Reference", f"Ø{dm:g}"), ("BarLength", tot / len(bars) * S)], tag)
            pset(e, "VE_MONGTRU", [("SoThanh", len(bars)), ("TongChieuDai_m", round(tot, 3)),
                                   ("KhoiLuong_kg", round(kg, 2))], tag)
    # lưới trục (cao độ mặt đất thiết kế: 0 / đáy bản đế thấp nhất)
    ux, vy = [], []
    for nm, a, b in sorted(sc.axes):
        pa = w(f"IFCCARTESIANPOINT(({f_(a[0] * S)},{f_(a[1] * S)}))")
        pb = w(f"IFCCARTESIANPOINT(({f_(b[0] * S)},{f_(b[1] * S)}))")
        ln = w(f"IFCPOLYLINE(({pa},{pb}))")
        ga = w(f"IFCGRIDAXIS({s_(nm)},{ln},.T.)")
        (ux if nm.startswith("X") else vy).append((ga, ln))
    if ux and vy:
        cs = w(f"IFCGEOMETRICCURVESET(({','.join(ln for _, ln in ux + vy)}))")
        rep = w(f"IFCSHAPEREPRESENTATION({c_foot},'FootPrint','GeometricCurveSet',({cs}))")
        layers["S-GRID"].append(rep)
        shp = w(f"IFCPRODUCTDEFINITIONSHAPE($,$,({rep}))")
        pl = w(f"IFCLOCALPLACEMENT({pl_st},{ax0})")
        grid = w(f"IFCGRID('{G('grid')}',{oh},{s_('Trục')},$,$,{pl},{shp},({','.join(a for a, _ in ux)}),"
                 f"({','.join(a for a, _ in vy)}),$,$)")
        elems.append(grid)
    w(f"IFCRELCONTAINEDINSPATIALSTRUCTURE('{G('contain')}',{oh},$,$,({','.join(elems)}),{st})")
    for nm, (m, objs) in mats.items():
        if objs:
            w(f"IFCRELASSOCIATESMATERIAL('{G('mat|' + nm)}',{oh},$,$,({','.join(objs)}),{m})")
    for nm, reps in layers.items():
        if reps:
            w(f"IFCPRESENTATIONLAYERASSIGNMENT({s_(nm)},$,({','.join(reps)}),$)")
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    head = ("ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('ViewDefinition [ReferenceView_V1.2]'),'2;1');\n"
            f"FILE_NAME({s_(path.replace(chr(92), '/').split('/')[-1])},'{ts}',(''),({s_('VE_MONGTRU')}),"
            f"'VE_MONGTRU {__version__}','VE_MONGTRU {__version__}','');\nFILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\n")
    body = "\n".join(f"#{i + 1}={r};" for i, r in enumerate(w.rows))
    with open(path, "w", encoding="ascii", newline="\n") as fh:
        fh.write(head + body + "\nENDSEC;\nEND-ISO-10303-21;\n")
