const express=require("express"), cors=require("cors");
const app=express(); app.use(cors());
app.get("/",(_req,res)=>res.send("<h1>ARK GUI</h1><p>Core on :3001</p>"));
app.listen(3000,()=>console.log("gui :3000"));
