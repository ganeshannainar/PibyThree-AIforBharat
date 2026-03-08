import { useState, useEffect } from 'react';
import { promotionsAPI } from '../../services/api';
import './Promotions.css';

const Promotions = () => {
  const [promotions, setPromotions] = useState([]);
  const [allPromotions, setAllPromotions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Edit modal state
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingPromotion, setEditingPromotion] = useState(null);
  const [editForm, setEditForm] = useState({
    headline: '',
    tagline: '',
    promotion_text: ''
  });
  const [saving, setSaving] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [generatingImage, setGeneratingImage] = useState(false);

  // AI Prompt customization state
  const [showPromptSettings, setShowPromptSettings] = useState(false);
  const [defaultPrompts, setDefaultPrompts] = useState({ text_prompt: '', image_prompt: '' });
  const [customTextPrompt, setCustomTextPrompt] = useState('');
  const [customImagePrompt, setCustomImagePrompt] = useState('');
  const [regenerateWithImage, setRegenerateWithImage] = useState(false);

  // Fetch default prompts on mount
  useEffect(() => {
    fetchDefaultPrompts();
  }, []);

  // Fetch all promotions on mount (for counts)
  useEffect(() => {
    fetchAllPromotions();
  }, []);

  // Fetch filtered promotions when filter changes
  useEffect(() => {
    fetchPromotions();
  }, [statusFilter]);

  const fetchDefaultPrompts = async () => {
    try {
      const response = await promotionsAPI.getDefaultPrompts();
      setDefaultPrompts(response.data);
    } catch (err) {
      console.error('Failed to fetch default prompts', err);
    }
  };

  const fetchAllPromotions = async () => {
    try {
      const response = await promotionsAPI.getAll(0, 100, null);
      setAllPromotions(response.data.data || []);
    } catch (err) {
      console.error('Failed to fetch all promotions', err);
    }
  };

  const fetchPromotions = async () => {
    setLoading(true);
    try {
      const response = await promotionsAPI.getAll(0, 50, statusFilter || null);
      setPromotions(response.data.data || []);
    } catch (err) {
      setError('Failed to fetch promotions');
      console.error(err);
    }
    setLoading(false);
  };

  const getCounts = () => {
    const normalize = (status) => status === 'active' ? 'live' : status;
    return {
      all: allPromotions.length,
      draft: allPromotions.filter(p => normalize(p.status) === 'draft').length,
      live: allPromotions.filter(p => normalize(p.status) === 'live').length,
      expired: allPromotions.filter(p => normalize(p.status) === 'expired').length,
    };
  };

  const counts = getCounts();

  const handleEdit = (promotion) => {
    setEditingPromotion(promotion);
    setEditForm({
      headline: promotion.headline || '',
      tagline: promotion.tagline || '',
      promotion_text: promotion.promotion_text || ''
    });
    // Reset prompt settings
    setCustomTextPrompt('');
    setCustomImagePrompt('');
    setRegenerateWithImage(false);
    setShowPromptSettings(false);
    setShowEditModal(true);
    setError('');
  };

  const handleSave = async () => {
    if (!editingPromotion) return;
    setSaving(true);
    setError('');
    try {
      await promotionsAPI.update(editingPromotion.id, editForm);
      setShowEditModal(false);
      fetchPromotions();
      fetchAllPromotions();
      alert('Promotion updated successfully!');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update promotion');
    }
    setSaving(false);
  };

  const handleRegenerate = async () => {
    if (!editingPromotion) return;
    setRegenerating(true);
    setError('');
    try {
      const response = await promotionsAPI.regenerate(editingPromotion.id, {
        customTextPrompt: customTextPrompt || null,
        customImagePrompt: customImagePrompt || null,
        regenerateImage: regenerateWithImage
      });

      // Update the form with new content
      setEditForm({
        headline: response.data.headline || editForm.headline,
        tagline: response.data.tagline || editForm.tagline,
        promotion_text: response.data.promotional_text || editForm.promotion_text
      });

      // Update promotion image if regenerated
      if (regenerateWithImage && response.data.image_url) {
        setEditingPromotion({
          ...editingPromotion,
          promotion_image_url: response.data.image_url
        });
      }

      const msg = regenerateWithImage
        ? 'Content & Image regenerated! Review and save when ready.'
        : 'Content regenerated! Review and save when ready.';
      alert(msg);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to regenerate content');
    }
    setRegenerating(false);
  };

  const handleGenerateImage = async () => {
    if (!editingPromotion) return;
    setGeneratingImage(true);
    setError('');
    try {
      const response = await promotionsAPI.generateImage(
        editingPromotion.id,
        customImagePrompt || null
      );

      if (response.data.success && response.data.image_url) {
        setEditingPromotion({
          ...editingPromotion,
          promotion_image_url: response.data.image_url
        });
        alert('Image generated successfully!\n' + response.data.message);
        fetchPromotions();
      } else {
        alert(response.data.message || 'Image generation completed');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate image');
    }
    setGeneratingImage(false);
  };

  const handleApprove = async (promotionId) => {
    if (!confirm('Make this promotion LIVE? It will appear on the homepage carousel.')) return;
    try {
      await promotionsAPI.approve(promotionId);
      fetchPromotions();
      fetchAllPromotions();
      alert('Promotion is now LIVE!');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to approve promotion');
    }
  };

  const handleDeactivate = async (promotionId) => {
    if (!confirm('Deactivate this promotion? It will be removed from the carousel.')) return;
    try {
      await promotionsAPI.deactivate(promotionId);
      fetchPromotions();
      fetchAllPromotions();
      alert('Promotion deactivated');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to deactivate');
    }
  };

  const handleDelete = async (promotionId) => {
    if (!confirm('Are you sure you want to delete this promotion? This action cannot be undone.')) return;
    try {
      await promotionsAPI.delete(promotionId);
      fetchPromotions();
      fetchAllPromotions();
      alert('Promotion deleted successfully');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete promotion');
    }
  };

  const handleReactivate = async (promotionId) => {
    if (!confirm('Reactivate this promotion? It will be live for 7 days.')) return;
    try {
      await promotionsAPI.reactivate(promotionId);
      fetchPromotions();
      fetchAllPromotions();
      alert('Promotion reactivated successfully');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reactivate promotion');
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      'draft': { class: 'badge-draft', text: '📝 Draft' },
      'live': { class: 'badge-live', text: '🟢 Live' },
      'expired': { class: 'badge-expired', text: '⏰ Expired' },
      'active': { class: 'badge-live', text: '🟢 Active' }
    };
    const badge = badges[status] || { class: 'badge-unknown', text: status };
    return <span className={`status-badge ${badge.class}`}>{badge.text}</span>;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  // Check if image is product thumbnail or AI-generated
  const isAIGeneratedImage = (promo) => {
    return promo.promotion_image_url &&
      promo.promotion_image_url !== promo.product_thumbnail &&
      promo.promotion_image_url.includes('/promotions/');
  };

  if (loading) {
    return <div className="promotions-loading">Loading promotions...</div>;
  }

  return (
    <div className="promotions-admin">
      <div className="promotions-header">
        <h1>🎯 Promotions Management</h1>
        <p className="subtitle">Manage AI-generated promotions before they go live</p>
      </div>

      {/* Dashboard Stats Bar */}
      <div className="promotions-dashboard">
        <div className="dashboard-stats">
          <div className="stat-card total">
            <div className="stat-icon">📋</div>
            <div className="stat-content">
              <span className="stat-count">{counts.all}</span>
              <span className="stat-label">Total Promotions</span>
            </div>
          </div>
          <div className="stat-card draft">
            <div className="stat-icon">📝</div>
            <div className="stat-content">
              <span className="stat-count">{counts.draft}</span>
              <span className="stat-label">Drafts</span>
            </div>
          </div>
          <div className="stat-card live">
            <div className="stat-icon">🟢</div>
            <div className="stat-content">
              <span className="stat-count">{counts.live}</span>
              <span className="stat-label">Live Now</span>
            </div>
          </div>
          <div className="stat-card expired">
            <div className="stat-icon">⏰</div>
            <div className="stat-content">
              <span className="stat-count">{counts.expired}</span>
              <span className="stat-label">Expired</span>
            </div>
          </div>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {/* Filter Tabs */}
      <div className="filter-tabs">
        <button
          className={`filter-tab ${statusFilter === '' ? 'active' : ''}`}
          onClick={() => setStatusFilter('')}
        >
          All ({counts.all})
        </button>
        <button
          className={`filter-tab ${statusFilter === 'draft' ? 'active' : ''}`}
          onClick={() => setStatusFilter('draft')}
        >
          📝 Draft ({counts.draft})
        </button>
        <button
          className={`filter-tab ${statusFilter === 'live' ? 'active' : ''}`}
          onClick={() => setStatusFilter('live')}
        >
          🟢 Live ({counts.live})
        </button>
        <button
          className={`filter-tab ${statusFilter === 'expired' ? 'active' : ''}`}
          onClick={() => setStatusFilter('expired')}
        >
          ⏰ Expired ({counts.expired})
        </button>
      </div>

      {/* Promotions Grid */}
      <div className="promotions-grid">
        {promotions.length === 0 ? (
          <div className="no-promotions">
            <p>No promotions found</p>
            <small>Promotions are created when you approve dynamic pricing for products</small>
          </div>
        ) : (
          promotions.map((promo) => (
            <div key={promo.id} className={`promotion-card status-${promo.status}`}>
              <div className="card-header">
                <div className="card-images">
                  <img
                    src={promo.product_thumbnail || '/placeholder.png'}
                    alt={promo.product_title}
                    className="product-thumb"
                  />
                  {isAIGeneratedImage(promo) && (
                    <div className="ai-image-indicator">🤖 AI Image</div>
                  )}
                </div>
                <div className="card-title-section">
                  <h3>{promo.product_title}</h3>
                  <span className="brand">{promo.product_brand}</span>
                  {getStatusBadge(promo.status)}
                </div>
              </div>

              <div className="card-pricing">
                <div className="price-row">
                  <span className="original-price">${promo.original_price?.toFixed(2)}</span>
                  <span className="arrow">→</span>
                  <span className="dynamic-price">${promo.dynamic_price?.toFixed(2)}</span>
                </div>
                <div className="discount-badge">
                  {promo.discount_percentage?.toFixed(1)}% OFF | Save ${promo.savings_amount?.toFixed(2)}
                </div>
              </div>

              <div className="card-content">
                <div className="content-item">
                  <label>Headline:</label>
                  <p className="headline-preview">{promo.headline || 'No headline'}</p>
                </div>
                <div className="content-item">
                  <label>Tagline:</label>
                  <p className="tagline-preview">{promo.tagline || 'No tagline'}</p>
                </div>
              </div>

              <div className="card-image-status">
                <span className={isAIGeneratedImage(promo) ? 'ai-generated' : 'product-image'}>
                  {isAIGeneratedImage(promo) ? '��️ Custom AI Banner' : '📷 Using Product Image'}
                </span>
              </div>

              <div className="card-meta">
                <span>Created: {formatDate(promo.created_at)}</span>
                {promo.expires_at && <span>Expires: {formatDate(promo.expires_at)}</span>}
              </div>

              <div className="card-actions">
                <button className="btn-edit" onClick={() => handleEdit(promo)}>
                  ✏️ Edit
                </button>

                {promo.status === 'draft' && (
                  <>
                    <button className="btn-approve" onClick={() => handleApprove(promo.id)}>
                      🚀 Go Live
                    </button>
                    <button className="btn-delete" onClick={() => handleDelete(promo.id)}>
                      🗑️ Delete
                    </button>
                  </>
                )}

                {promo.status === 'live' && (
                  <>
                    <button className="btn-deactivate" onClick={() => handleDeactivate(promo.id)}>
                      ⏸️ Deactivate
                    </button>
                    <button className="btn-delete" onClick={() => handleDelete(promo.id)}>
                      🗑️ Delete
                    </button>
                  </>
                )}

                {(promo.status === 'expired' || promo.status === 'deactivated') && (
                  <>
                    <button className="btn-reactivate" onClick={() => handleReactivate(promo.id)}>
                      🔄 Reactivate
                    </button>
                    <button className="btn-delete" onClick={() => handleDelete(promo.id)}>
                      🗑️ Delete
                    </button>
                  </>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Enhanced Edit Modal */}
      {showEditModal && editingPromotion && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal-content edit-modal enhanced" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>✏️ Edit Promotion</h2>
              <button className="close-btn" onClick={() => setShowEditModal(false)}>×</button>
            </div>

            <div className="modal-body">
              {/* Product Info Banner */}
              <div className="product-info-banner">
                <img
                  src={editingPromotion.product_thumbnail || '/placeholder.png'}
                  alt={editingPromotion.product_title}
                />
                <div>
                  <h3>{editingPromotion.product_title}</h3>
                  <span className="brand">{editingPromotion.product_brand}</span>
                  <div className="price-info">
                    ${editingPromotion.original_price?.toFixed(2)} →
                    <strong> ${editingPromotion.dynamic_price?.toFixed(2)}</strong>
                    <span className="discount"> ({editingPromotion.discount_percentage?.toFixed(1)}% OFF)</span>
                  </div>
                </div>
              </div>

              {error && <div className="modal-error">{error}</div>}

              {/* === PROMOTIONAL IMAGE SECTION === */}
              <div className="section-divider">
                <h4>🖼️ Promotional Image</h4>
              </div>

              <div className="image-section">
                <div className="current-image">
                  <img
                    src={editingPromotion.promotion_image_url || editingPromotion.product_thumbnail || '/placeholder.png'}
                    alt="Promotion Banner"
                    className="promotion-image-preview"
                  />
                  <div className="image-status">
                    {isAIGeneratedImage(editingPromotion)
                      ? <span className="badge-ai">🤖 AI Generated Banner</span>
                      : <span className="badge-product">📷 Product Thumbnail (No AI image yet)</span>
                    }
                  </div>
                </div>

                <button
                  className="btn-generate-image"
                  onClick={handleGenerateImage}
                  disabled={generatingImage || regenerating}
                >
                  {generatingImage ? '🔄 Generating Image...' : '🖼️ Generate AI Banner Image'}
                </button>
              </div>

              {/* === GENERATED CONTENT SECTION === */}
              <div className="section-divider">
                <h4>📝 Generated Content</h4>
              </div>

              <div className="form-group">
                <label>Headline</label>
                <input
                  type="text"
                  value={editForm.headline}
                  onChange={(e) => setEditForm({ ...editForm, headline: e.target.value })}
                  placeholder="Enter catchy headline..."
                  maxLength={100}
                />
                <small>{editForm.headline.length}/100 characters</small>
              </div>

              <div className="form-group">
                <label>Tagline</label>
                <input
                  type="text"
                  value={editForm.tagline}
                  onChange={(e) => setEditForm({ ...editForm, tagline: e.target.value })}
                  placeholder="Enter engaging tagline..."
                  maxLength={150}
                />
                <small>{editForm.tagline.length}/150 characters</small>
              </div>

              <div className="form-group">
                <label>Promotional Text</label>
                <textarea
                  value={editForm.promotion_text}
                  onChange={(e) => setEditForm({ ...editForm, promotion_text: e.target.value })}
                  placeholder="Enter promotional description..."
                  rows={3}
                  maxLength={500}
                />
                <small>{editForm.promotion_text.length}/500 characters</small>
              </div>

              {/* === AI PROMPT CUSTOMIZATION SECTION === */}
              <div className="section-divider">
                <h4
                  className="collapsible-header"
                  onClick={() => setShowPromptSettings(!showPromptSettings)}
                >
                  🤖 AI Prompt Settings {showPromptSettings ? '▼' : '▶'}
                </h4>
                <small className="section-hint">
                  Customize AI instructions for regeneration
                </small>
              </div>

              {showPromptSettings && (
                <div className="prompt-settings">
                  <div className="prompt-info-box">
                    <p>💡 <strong>How it works:</strong> Leave empty to use default prompts, or customize below to guide AI output.</p>
                  </div>

                  <div className="form-group">
                    <label>
                      📝 Text Generation Prompt
                      <button
                        className="btn-use-default"
                        onClick={() => setCustomTextPrompt(defaultPrompts.text_prompt)}
                      >
                        Load Default
                      </button>
                    </label>
                    <textarea
                      value={customTextPrompt}
                      onChange={(e) => setCustomTextPrompt(e.target.value)}
                      placeholder="Custom instructions for headline, tagline, and promo text generation...

Example: 'Make it playful and target young audience. Use Gen-Z language. Focus on FOMO.'"
                      rows={5}
                    />
                    <small>Leave empty to use default prompt</small>
                  </div>

                  <div className="form-group">
                    <label>
                      🖼️ Image Generation Prompt
                      <button
                        className="btn-use-default"
                        onClick={() => setCustomImagePrompt(defaultPrompts.image_prompt)}
                      >
                        Load Default
                      </button>
                    </label>
                    <textarea
                      value={customImagePrompt}
                      onChange={(e) => setCustomImagePrompt(e.target.value)}
                      placeholder="Custom instructions for banner image generation...

Example: 'Minimalist design, use blue gradient, show product prominently, luxury feel'"
                      rows={4}
                    />
                    <small>Leave empty to use default prompt</small>
                  </div>

                  <div className="form-group checkbox-group">
                    <label>
                      <input
                        type="checkbox"
                        checked={regenerateWithImage}
                        onChange={(e) => setRegenerateWithImage(e.target.checked)}
                      />
                      Also regenerate image when regenerating content
                    </label>
                  </div>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button
                className="btn-regenerate"
                onClick={handleRegenerate}
                disabled={regenerating || saving || generatingImage}
              >
                {regenerating ? '🔄 Regenerating...' : '🤖 Regenerate Content'}
              </button>
              <div className="footer-right">
                <button
                  className="btn-cancel"
                  onClick={() => setShowEditModal(false)}
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  className="btn-save"
                  onClick={handleSave}
                  disabled={saving || regenerating || generatingImage}
                >
                  {saving ? 'Saving...' : '💾 Save Changes'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Promotions;
