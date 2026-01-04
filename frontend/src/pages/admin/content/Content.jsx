import React, { useState, useEffect } from 'react';
import contentApi from '../../../api/contentApi';
import './Content.css';

const Content = () => {
  // STATE CHUNG 
  const [activeTab, setActiveTab] = useState('pages');
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState('list');

  // STATE BÀI VIẾT 
  const [posts, setPosts] = useState([]);
  const [formData, setFormData] = useState({
    id: null, title: '', slug: '', content: '', excerpt: '',
    featured_image: '', meta_title: '', meta_description: '',
    meta_keywords: '', template: 'default', is_published: true
  });

  //STATE BANNER (FULL OPTIONS) 
  const [banners, setBanners] = useState([]);
  const [bannerForm, setBannerForm] = useState({
      banner_id: null,
      title: '',
      description: '',
      image_url: '',
      mobile_image_url: '',
      link_url: '',
      button_text: 'Mua ngay',
      display_order: 1,
      is_active: true,
      start_date: '',
      end_date: ''
  });
  const [uploading, setUploading] = useState(false);

  //  LOAD DỮ LIỆU
  const fetchData = async () => {
    setLoading(true);
    try {
        if (activeTab === 'pages') {
            const res = await contentApi.getAll({ page: 1, page_size: 100, _t: Date.now() });
            let list = [];
            if (Array.isArray(res)) list = res;
            else if (res && res.data) list = Array.isArray(res.data) ? res.data : (res.data.items || []);
            else if (res && res.items) list = res.items;
            setPosts(list);
        } else {
            console.log(" Gọi API Banner...");
            let res = await contentApi.getBanners();
            console.log(" API Trả về:", res);

            //  Nếu API trả về null/undefined -> Ép thành mảng rỗng
            if (!res) res = []; 

            let list = [];
            if (Array.isArray(res)) list = res;
            else if (res.data && Array.isArray(res.data)) list = res.data;
            else if (res.items && Array.isArray(res.items)) list = res.items;
            else if (res.result && Array.isArray(res.result)) list = res.result;

            if (list.length > 0) {
                setBanners(list.sort((a, b) => (a.display_order || 0) - (b.display_order || 0)));
            } else {
                setBanners([]);
            }
        }
    } catch (error) {
        console.error("Lỗi tải dữ liệu:", error);
    } finally {
        setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [activeTab]);

  // XỬ LÝ FORM BÀI VIẾT
  const handlePageSubmit = async (e) => {
    e.preventDefault(); setLoading(true);
    try {
        const payload = { ...formData, id: undefined };
        if (formData.id) await contentApi.update(formData.id, payload);
        else await contentApi.create(payload);
        alert("Thành công!"); setView('list'); fetchData();
    } catch (err) { alert("Lỗi: " + err.message); } finally { setLoading(false); }
  };
  const handlePageDelete = async (id) => { if(window.confirm("Xóa bài này?")) { try{await contentApi.remove(id); fetchData();}catch(e){} } };
  const togglePageStatus = async (post) => { try{ const id=post.id||post.page_id; if(post.is_published)await contentApi.unpublish(id);else await contentApi.publish(id); fetchData();}catch(e){} };

  // XỬ LÝ FORM BANNER
  
  const handleUpload = async (e, field) => {
      const file = e.target.files[0]; if(!file) return; setUploading(true);
      try {
          // Gọi API upload (đã fix header)
          const res = await contentApi.uploadFile(file);
          // Lấy url từ response (chấp nhận nhiều định dạng trả về)
          const url = res.url || res.image_url || res.data?.url || (typeof res === 'string' ? res : null);
          
          if(url) {
              setBannerForm(prev => ({...prev, [field]: url}));
          } else {
              alert("Lỗi: Không lấy được link ảnh từ server.");
          }
      } catch(e){ 
          console.error(e);
          alert("Lỗi upload ảnh! Kiểm tra lại file hoặc server."); 
      } finally{setUploading(false);}
  };

  const handleBannerSubmit = async (e) => {
      e.preventDefault(); setLoading(true);
      try {
          // Xử lý ngày tháng: Nếu rỗng thì gửi null để Backend không chặn
          const payload = {
              ...bannerForm,
              start_date: bannerForm.start_date ? bannerForm.start_date : null,
              end_date: bannerForm.end_date ? bannerForm.end_date : null,
              banner_id: undefined 
          };

          if(bannerForm.banner_id) await contentApi.updateBanner(bannerForm.banner_id, payload);
          else await contentApi.createBanner(payload);

          alert("Lưu banner thành công!"); setView('list'); fetchData();
      } catch(e){ alert("Lỗi: "+e.message); } finally{setLoading(false);}
  };

  const handleBannerDelete = async (id) => { if(window.confirm("Xóa banner này?")) { try{await contentApi.deleteBanner(id); fetchData();}catch(e){} } };

  return (
    <div className="content-page">
      <div className="page-header"><h2>CMS & Quảng cáo</h2></div>

      <div className="tabs-header" style={{display:'flex', gap:'20px', borderBottom:'2px solid #eee', marginBottom:'20px'}}>
          <div className={`tab-item ${activeTab==='pages'?'active-tab':''}`} onClick={()=>{setActiveTab('pages');setView('list')}} style={{padding:'10px',cursor:'pointer',fontWeight:activeTab==='pages'?'bold':'normal', borderBottom:activeTab==='pages'?'3px solid #000':'none'}}>Bài viết</div>
          <div className={`tab-item ${activeTab==='banners'?'active-tab':''}`} onClick={()=>{setActiveTab('banners');setView('list')}} style={{padding:'10px',cursor:'pointer',fontWeight:activeTab==='banners'?'bold':'normal', borderBottom:activeTab==='banners'?'3px solid #000':'none'}}>Banner Slide</div>
      </div>

      <div className="toolbar" style={{display:'flex', justifyContent:'flex-end', marginBottom:'20px'}}>
         {view === 'list' ?
            <button className="btn-create" onClick={()=>{
                if(activeTab==='pages') setFormData({id:null, title:'', slug:'', content:'', is_published:true});
                else setBannerForm({banner_id:null, title:'', description:'', image_url:'', mobile_image_url:'', link_url:'', button_text:'Mua ngay', display_order:1, is_active:true, start_date:'', end_date:''});
                setView('editor');
            }}>+ Thêm mới</button> :
            <button className="btn-back" onClick={()=>setView('list')}>Quay lại</button>
         }
      </div>

      {activeTab === 'pages' && view === 'list' && (
          <div className="table-container animate-pop-in">
                <table>
                    <thead><tr><th>Tiêu đề</th><th>Ngày tạo</th><th>Trạng thái</th><th>Hành động</th></tr></thead>
                    <tbody>
                        {posts.map(p => { const id=p.id||p.page_id; return (
                            <tr key={id||Math.random()}>
                                <td><b>{p.title}</b><br/><small>{p.slug}</small></td>
                                <td>{p.created_at?new Date(p.created_at).toLocaleDateString('vi-VN'):'-'}</td>
                                <td><button className={`status-badge ${p.is_published?'active':'draft'}`} onClick={()=>togglePageStatus(p)}>{p.is_published?'Đã đăng':'Nháp'}</button></td>
                                <td><button className="btn-action edit" onClick={()=>{setFormData({...p,id:id});setView('editor')}}>Sửa</button><button className="btn-action delete" onClick={()=>handlePageDelete(id)}>Xóa</button></td>
                            </tr>
                        )})}
                        {posts.length===0 && <tr><td colSpan="4" className="text-center">Chưa có bài viết.</td></tr>}
                    </tbody>
                </table>
          </div>
      )}

      {activeTab === 'banners' && view === 'list' && (
            <div className="table-container animate-pop-in">
                <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(300px, 1fr))', gap:'20px'}}>
                    {banners.map(b => (
                        <div key={b.banner_id} style={{border:'1px solid #ddd', borderRadius:'8px', overflow:'hidden', background:'white'}}>
                            <div style={{height:'150px', background:'#eee', position:'relative'}}>
                                <img src={b.image_url} alt={b.title} style={{width:'100%', height:'100%', objectFit:'cover'}} onError={(e)=>e.target.src='https://via.placeholder.com/300x150?text=No+Image'}/>
                                <div style={{position:'absolute', top:5, right:5, background: b.is_active?'#10b981':'#6b7280', color:'white', fontSize:'10px', padding:'2px 6px', borderRadius:'4px'}}>{b.is_active?'Active':'Inactive'}</div>
                            </div>
                            <div style={{padding:'10px'}}>
                                <b>{b.title}</b>
                                <div style={{fontSize:'12px', color:'#666', margin:'5px 0'}}>{b.start_date ? `📅 ${new Date(b.start_date).toLocaleDateString()}` : '∞ Luôn hiện'}</div>
                                <div style={{display:'flex', justifyContent:'space-between', marginTop:'10px', borderTop:'1px solid #eee', paddingTop:'10px'}}>
                                    <span style={{fontSize:'12px'}}>TT: {b.display_order}</span>
                                    <div><button className="btn-action edit" onClick={()=>{
                                        const formatD = (d) => d ? new Date(d).toISOString().slice(0,16) : '';
                                        setBannerForm({...b, start_date: formatD(b.start_date), end_date: formatD(b.end_date)});
                                        setView('editor');
                                    }}>Sửa</button><button className="btn-action delete" onClick={()=>handleBannerDelete(b.banner_id)}>Xóa</button></div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
                {banners.length === 0 && <div className="text-center" style={{padding:'30px', color:'#888'}}>Chưa có banner nào.</div>}
            </div>
      )}

      {view === 'editor' && (
         <div className="editor-container animate-pop-in">
             <div className="card-header"><h3>{activeTab==='pages' ? (formData.id?'Sửa bài':'Bài mới') : (bannerForm.banner_id?'Sửa Banner':'Thêm Banner')}</h3></div>
             <div className="card-body">
                {activeTab === 'pages' ? (
                    <form onSubmit={handlePageSubmit}>
                        <div className="form-group"><label>Tiêu đề *</label><input type="text" className="input-title" value={formData.title} onChange={e=>{const s=e.target.value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9\s-]/g,"").replace(/\s+/g,"-"); setFormData({...formData,title:e.target.value,slug:!formData.id?s:formData.slug})}} required/></div>
                        <div className="form-group"><label>Slug</label><input type="text" className="input-title" value={formData.slug} onChange={e=>setFormData({...formData,slug:e.target.value})}/></div>
                        <div className="form-group"><label>Nội dung</label><textarea className="input-content" rows="10" value={formData.content} onChange={e=>setFormData({...formData,content:e.target.value})}></textarea></div>
                        <div className="editor-footer"><label><input type="checkbox" checked={formData.is_published} onChange={e=>setFormData({...formData,is_published:e.target.checked})}/> Đăng ngay</label><button type="submit" className="btn-publish">Lưu</button></div>
                    </form>
                ) : (
                    <form onSubmit={handleBannerSubmit}>
                        <div className="form-group"><label>Tiêu đề *</label><input type="text" className="input-title" value={bannerForm.title} onChange={e=>setBannerForm({...bannerForm,title:e.target.value})} required/></div>
                        <div className="form-group"><label>Mô tả</label><textarea className="input-title" style={{height:'60px'}} value={bannerForm.description || ''} onChange={e=>setBannerForm({...bannerForm,description:e.target.value})}/></div>
                        
                        <div className="form-group" style={{background:'#f9f9f9', padding:'10px', borderRadius:'6px'}}>
                            <label>Ảnh PC (Desktop)</label>
                            {bannerForm.image_url && <img src={bannerForm.image_url} alt="Preview" style={{height:'80px', display:'block', marginBottom:'5px', border:'1px solid #ddd'}}/>}
                            <div style={{display:'flex', gap:'10px'}}><input type="text" className="input-title" value={bannerForm.image_url} onChange={e=>setBannerForm({...bannerForm,image_url:e.target.value})} placeholder="Link ảnh PC..." style={{flex:1}}/><label className="btn-create" style={{cursor:'pointer'}}>{uploading?'...':'Upload'}<input type="file" onChange={(e)=>handleUpload(e, 'image_url')} style={{display:'none'}}/></label></div>
                        </div>

                        <div className="form-group" style={{background:'#f9f9f9', padding:'10px', borderRadius:'6px', marginTop:'10px'}}>
                            <label>Ảnh Mobile (Tùy chọn)</label>
                            {bannerForm.mobile_image_url && <img src={bannerForm.mobile_image_url} alt="Preview" style={{height:'80px', display:'block', marginBottom:'5px', border:'1px solid #ddd'}}/>}
                            <div style={{display:'flex', gap:'10px'}}><input type="text" className="input-title" value={bannerForm.mobile_image_url || ''} onChange={e=>setBannerForm({...bannerForm,mobile_image_url:e.target.value})} placeholder="Link ảnh Mobile..." style={{flex:1}}/><label className="btn-create" style={{cursor:'pointer'}}>{uploading?'...':'Upload'}<input type="file" onChange={(e)=>handleUpload(e, 'mobile_image_url')} style={{display:'none'}}/></label></div>
                        </div>

                        <div className="form-group"><label>Link đích</label><input type="text" className="input-title" value={bannerForm.link_url || ''} onChange={e=>setBannerForm({...bannerForm,link_url:e.target.value})}/></div>
                        
                        <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:'20px'}}>
                            <div className="form-group"><label>Ngày bắt đầu</label><input type="datetime-local" className="input-title" value={bannerForm.start_date || ''} onChange={e=>setBannerForm({...bannerForm,start_date:e.target.value})}/></div>
                            <div className="form-group"><label>Ngày kết thúc</label><input type="datetime-local" className="input-title" value={bannerForm.end_date || ''} onChange={e=>setBannerForm({...bannerForm,end_date:e.target.value})}/></div>
                        </div>

                        <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:'20px'}}>
                            <div className="form-group"><label>Thứ tự</label><input type="number" className="input-title" value={bannerForm.display_order} onChange={e=>setBannerForm({...bannerForm,display_order:parseInt(e.target.value)})}/></div>
                            <div className="form-group"><label>Nút bấm</label><input type="text" className="input-title" value={bannerForm.button_text || ''} onChange={e=>setBannerForm({...bannerForm,button_text:e.target.value})}/></div>
                        </div>
                        
                        <div className="editor-footer"><label><input type="checkbox" checked={bannerForm.is_active} onChange={e=>setBannerForm({...bannerForm,is_active:e.target.checked})}/> Hiển thị ngay</label><button type="submit" className="btn-publish">Lưu Banner</button></div>
                    </form>
                )}
             </div>
         </div>
      )}
    </div>
  );
};

export default Content;