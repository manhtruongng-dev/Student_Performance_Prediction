import React, {useEffect, useMemo, useState} from "react";
import {Routes, Route, NavLink, useLocation} from "react-router-dom";
import {Home, BrainCircuit, Info, History, Upload, Menu, Activity, Download, RotateCcw} from "lucide-react";
import studentLogo from "./assets/student-logo.png";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function api(path, options={}) {
  const r = await fetch(`${API}${path}`, options);
  if (!r.ok) {
    let msg = `HTTP ${r.status}`;
    try { const j = await r.json(); msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail); } catch {}
    throw new Error(msg);
  }
  return r;
}

const fields = [
  ["G1","Điểm giữa kỳ 1",3,19],["G2","Điểm giữa kỳ 2",0,19],["failures","Số lần trượt",0,3],
  ["age","Tuổi",15,22],["traveltime","Thời gian đi lại (1-4)",1,4],["goout","Mức độ đi chơi (1-5)",1,5],
  ["studytime","Thời gian học (1-4)",1,4],["Medu","Học vấn mẹ (0-4)",0,4],["Fedu","Học vấn cha (0-4)",0,4],
  ["absences","Số buổi vắng",0,75]
];
const defaults = {G1:15,G2:14,failures:0,age:17,traveltime:1,goout:2,studytime:2,Medu:4,Fedu:4,absences:2};

function Layout({children, online}) {
  const [open,setOpen]=useState(false);
  const loc=useLocation();
  const nav=[
    ["/","Trang chủ",Home],["/predict","Dự đoán",BrainCircuit],["/model","Thông tin model",Info],
    ["/history","Lịch sử",History],["/batch","Dự đoán hàng loạt",Upload]
  ];
  const title=nav.find(x=>x[0]===loc.pathname)?.[1] || "Trang chủ";
  return <div className="app">
    <aside className={open?"sidebar open":"sidebar"}>
      <div className="brand"><div className="brand-logo"><img src={studentLogo} alt="Student Logo" /></div><b>Student Performance<br/>Prediction</b></div>
      <nav>{nav.map(([to,label,Icon])=><NavLink key={to} to={to} end={to==="/"} onClick={()=>setOpen(false)}><Icon size={18}/><span>{label}</span></NavLink>)}</nav>
      <div className="sidefoot">Hệ thống dự đoán G3</div>
    </aside>
    <main>
      <header><button className="menubtn" onClick={()=>setOpen(!open)}><Menu/></button><strong>{title}</strong><div className={online?"status online":"status offline"}><span/>API {online?"Online":"Offline"}</div></header>
      <div className="content">{children}</div>
    </main>
  </div>
}

function Card({children,className=""}) { return <section className={`card ${className}`}>{children}</section> }
function Metric({label,value,sub}) { return <Card><div className="muted">{label}</div><div className="metric">{value}</div><small>{sub}</small></Card> }

function Dashboard({info,history}) {
  const metrics=info?.metrics||{};
  const recent=history.slice(0,5);
  return <>
    <div className="pagehead"><div><h1>Tổng quan hệ thống</h1><p>Hệ thống dự đoán kết quả học tập cuối kỳ (G3)</p></div></div>
    <div className="metrics">
      <Metric label="R² (Test)" value={metrics.R2?.toFixed?.(4) ?? metrics.r2?.toFixed?.(4) ?? "0.8611"} sub="Mức độ giải thích biến thiên"/>
      <Metric label="RMSE" value={metrics.RMSE?.toFixed?.(4) ?? metrics.rmse?.toFixed?.(4) ?? "1.6876"} sub="Thấp hơn là tốt"/>
      <Metric label="MAE" value={metrics.MAE?.toFixed?.(4) ?? metrics.mae?.toFixed?.(4) ?? "1.0848"} sub="Sai số tuyệt đối trung bình"/>
      <Metric label="Trạng thái model" value="Ready" sub={info?.model_name||"Random Forest"}/>
    </div>
    <div className="grid2">
      <Card><h3>Thông tin mô hình</h3><div className="bigmodel">🌲 Random Forest Regressor</div><p>Mô hình Random Forest được sử dụng để dự đoán điểm cuối kỳ (G3) dựa trên dữ liệu học tập của học sinh. Kết quả dự đoán được tạo trực tiếp từ mô hình đã huấn luyện <code>best_model_package.joblib</code> , hỗ trợ đánh giá sớm kết quả học tập của học sinh.</p></Card>
      <Card><h3>Luồng dự đoán</h3><div className="flow">10 trường đầu vào <b>→</b> Feature Engineering <b>→</b> 11 đặc trưng model <b>→</b> G3</div><p><code>absences</code> được dùng để tạo <code>study_per_absence</code> và <code>failure_impact</code>.</p></Card>
    </div>
    <Card><div className="cardtitle"><h3>Hoạt động gần đây</h3><NavLink to="/history">Xem tất cả →</NavLink></div>
      {recent.length?<Table rows={recent}/>:<Empty text="Chưa có lần dự đoán nào."/>}
    </Card>
  </>
}

function Table({rows}) {
 return <div className="tablewrap"><table><thead><tr><th>#</th><th>Thời gian</th><th>Đầu vào chính</th><th>Dự đoán G3</th><th>Model</th></tr></thead>
 <tbody>{rows.map(x=><tr key={x.id}><td>{x.id}</td><td>{new Date(x.created_at).toLocaleString("vi-VN")}</td><td>G1: {x.inputs.G1}, G2: {x.inputs.G2}, Absences: {x.inputs.absences}</td><td><b>{Number(x.predicted_g3).toFixed(2)}</b></td><td>Random Forest</td></tr>)}</tbody></table></div>
}
function Empty({text}) {return <div className="empty">{text}</div>}

function Predict({onDone}) {
 const [form,setForm]=useState(defaults), [result,setResult]=useState(null), [loading,setLoading]=useState(false), [error,setError]=useState("");
 const submit=async e=>{e.preventDefault();setError("");setLoading(true);try{
   const payload=Object.fromEntries(Object.entries(form).map(([k,v])=>[k,Number(v)]));
   const r=await api("/predict",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
   const j=await r.json(); setResult(j); onDone?.();
 }catch(e){setError(e.message)}finally{setLoading(false)}};
 return <>
  <div className="pagehead"><div><h1>Dự đoán điểm G3</h1><p>Nhập 10 thông tin đầu vào để dự đoán điểm cuối kỳ</p></div></div>
  <div className="predictgrid"><Card><form onSubmit={submit}><h3>Thông tin học sinh</h3><div className="formgrid">
   {fields.map(([k,label,min,max])=><label key={k}>{label}<input type="number" min={min} max={max} required value={form[k]} onChange={e=>setForm({...form,[k]:e.target.value})}/><small>Khoảng hợp lệ: {min}–{max}</small></label>)}
  </div>{error&&<div className="error">{error}</div>}<div className="actions"><button type="button" className="secondary" onClick={()=>{setForm(defaults);setResult(null)}}><RotateCcw size={16}/> Làm mới</button><button disabled={loading}>{loading?"Đang dự đoán...":"Dự đoán"}</button></div></form></Card>
  <Card className="resultcard"><h3>Kết quả dự đoán</h3>{result?<><div className="score">{Number(result.predicted_g3).toFixed(2)}<span>/20</span></div><p>Điểm G3 dự đoán</p><div className="success">✓ Kết quả dự đoán được tạo bởi mô hình học máy và chỉ mang tính tham khảo.</div><small>Mã dự đoán: #{result.prediction_id}</small></>:<Empty text="Nhập thông tin và nhấn Dự đoán để xem kết quả."/ >}</Card></div>
 </>
}

function ModelInfo({info}) {
 const m=info?.metrics||{};
 return <><div className="pagehead"><div><h1>Thông tin mô hình</h1><p>Chi tiết về mô hình và hiệu suất</p></div></div>
 <Card><h3>Thông tin chung</h3><div className="infogrid"><div><span>Tên mô hình</span><b>{info?.model_name||"RandomForest_Tuned"}</b></div><div><span>Loại bài toán</span><b>Regression</b></div><div><span>Biến mục tiêu</span><b>G3 (Điểm cuối kỳ)</b></div><div><span>Khoảng giá trị</span><b>0–20</b></div></div></Card>
 <div className="metrics"><Metric label="R² (Test)" value={m.R2??m.r2??0.8611}/><Metric label="RMSE" value={m.RMSE??m.rmse??1.6876}/><Metric label="MAE" value={m.MAE??m.mae??1.0848}/></div>
 <div className="grid2"><Card><h3>Đầu vào API/Form (10 trường)</h3><div className="chips">{(info?.raw_input_fields||fields.map(x=>x[0])).map(x=><span key={x}>{x}</span>)}</div></Card>
 <Card><h3>Đặc trưng model (11 features)</h3><div className="chips">{(info?.final_model_features||[]).map(x=><span key={x}>{x}</span>)}</div></Card></div>
 <Card><h3>Mô tả</h3><p>Mô hình Random Forest được xây dựng nhằm dự đoán điểm cuối kỳ (G3) dựa trên kết quả học tập G1, G2 cùng các đặc trưng liên quan đến quá trình học tập của học sinh. Các đặc trưng bổ sung được tự động xử lý và tính toán trước khi đưa vào mô hình, giúp đảm bảo dữ liệu đầu vào nhất quán và hỗ trợ nâng cao hiệu quả dự đoán.</p></Card></>
}

function HistoryPage({history,refresh}) {
 useEffect(()=>{refresh()},[]);
 return <><div className="pagehead"><div><h1>Lịch sử dự đoán</h1><p>Danh sách các lần dự đoán đã được lưu trong SQLite</p></div><button onClick={refresh}>Làm mới</button></div><Card>{history.length?<Table rows={history}/>:<Empty text="Chưa có dữ liệu lịch sử."/ >}</Card></>
}

function Batch() {
 const [file,setFile]=useState(null),[rows,setRows]=useState([]),[blob,setBlob]=useState(null),[error,setError]=useState(""),[loading,setLoading]=useState(false);
 const upload=async()=>{if(!file)return;setLoading(true);setError("");try{
   const fd=new FormData();fd.append("file",file);const r=await api("/predict/batch",{method:"POST",body:fd});const b=await r.blob();setBlob(b);
   const text=await b.text();const lines=text.trim().split(/\r?\n/);const headers=lines[0].split(",");
   setRows(lines.slice(1).map(line=>{const vals=line.split(",");return Object.fromEntries(headers.map((h,i)=>[h,vals[i]]))}));
 }catch(e){setError(e.message)}finally{setLoading(false)}};
 const download=()=>{if(!blob)return;const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="predictions.csv";a.click();URL.revokeObjectURL(a.href)};
 return <><div className="pagehead"><div><h1>Dự đoán hàng loạt</h1><p>Upload CSV để dự đoán nhiều học sinh cùng lúc</p></div></div>
 <div className="grid2"><Card><h3>1. Upload file CSV</h3><label className="drop"><Upload size={42}/><b>{file?file.name:"Chọn hoặc kéo thả file CSV"}</b><input type="file" accept=".csv,text/csv" onChange={e=>{setFile(e.target.files[0]);setRows([]);setBlob(null)}}/></label>
 <p className="muted">Cột bắt buộc: G1, G2, failures, age, traveltime, goout, studytime, Medu, Fedu, absences.</p>{error&&<div className="error">{error}</div>}<button disabled={!file||loading} onClick={upload}>{loading?"Đang xử lý...":"Dự đoán hàng loạt"}</button></Card>
 <Card><h3>2. Kết quả dự đoán</h3>{rows.length?<><div className="tablewrap"><table><thead><tr><th>#</th><th>G1</th><th>G2</th><th>Absences</th><th>Dự đoán G3</th></tr></thead><tbody>{rows.map((r,i)=><tr key={i}><td>{i+1}</td><td>{r.G1}</td><td>{r.G2}</td><td>{r.absences}</td><td><b>{Number(r.predicted_g3).toFixed(2)}</b></td></tr>)}</tbody></table></div><button onClick={download}><Download size={16}/> Tải kết quả CSV</button></>:<Empty text="Kết quả sẽ hiển thị tại đây sau khi xử lý CSV."/ >}</Card></div></>
}

export default function App(){
 const [online,setOnline]=useState(false),[info,setInfo]=useState(null),[history,setHistory]=useState([]);
 const refresh=async()=>{try{const r=await api("/history?limit=200&offset=0");setHistory(await r.json())}catch{}};
 useEffect(()=>{(async()=>{try{await api("/health");setOnline(true);const r=await api("/model-info");setInfo(await r.json());await refresh()}catch{setOnline(false)}})()},[]);
 return <Layout online={online}><Routes>
  <Route path="/" element={<Dashboard info={info} history={history}/>}/>
  <Route path="/predict" element={<Predict onDone={refresh}/>}/>
  <Route path="/model" element={<ModelInfo info={info}/>}/>
  <Route path="/history" element={<HistoryPage history={history} refresh={refresh}/>}/>
  <Route path="/batch" element={<Batch/>}/>
 </Routes></Layout>
}