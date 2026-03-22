// Complete Translation data for all languages
const translations = {
    vi: {
        // Navigation
        nav_home: 'Trang chủ',
        nav_news: 'Tin tức',
        nav_blog: 'Blog',
        nav_mode: 'Chế độ',
        nav_account: 'Tài khoản',
        nav_login: 'Đăng nhập',
        nav_logout: 'Đăng xuất',
        lang_name: 'Tiếng Việt',
        donate_header: 'Ủng hộ chúng tôi',
        
        // Hero Section
        hero_title_prefix: 'Tải Video',
        hero_title_suffix: 'Nhanh Chóng',
        hero_subtitle: 'Chuyển đổi video từ YouTube & TikTok sang MP4, MP3 chất lượng cao - Miễn phí & Không giới hạn',
        stats_downloads: 'lượt tải đã xử lý',
        
        // Tabs
        tab_youtube: 'YouTube',
        tab_youtube_hint: 'Tải video & nhạc từ YouTube',
        tab_tiktok: 'TikTok',
        tab_tiktok_hint: 'Tải video & ảnh từ TikTok',
        
        // Cards
        card_title_youtube: 'Tải Video YouTube',
        card_desc_youtube: 'Dán link video YouTube để tải xuống',
        card_title_tiktok: 'Tải Video TikTok',
        card_desc_tiktok: 'Dán link video TikTok để tải xuống',
        
        // Input & Buttons
        input_placeholder_youtube: 'Dán link YouTube tại đây...',
        input_placeholder_tiktok: 'Dán link TikTok tại đây...',
        btn_paste: 'Dán',
        btn_download: 'Tải Xuống',
        btn_download_again: 'Tải Lại',
        
        // Quality & Format
        quality_label: 'Chọn định dạng:',
        format_video: 'Video',
        format_audio: 'Âm thanh',
        quality_best: 'Tốt nhất',
        quality_high: 'Cao',
        quality_medium: 'Trung bình',
        
        // Gallery
        select_images_prompt: 'Chọn ảnh để tải:',
        select_all: 'Chọn tất cả',
        deselect_all: 'Bỏ chọn tất cả',
        
        // Progress
        progress_preparing: 'Đang chuẩn bị...',
        progress_downloading: 'Đang tải...',
        progress_processing: 'Đang xử lý...',
        progress_completed: 'Hoàn tất!',
        download_complete: '✅ Tải xuống hoàn tất! File đang được lưu...',
        
        // Features
        feature_fast: 'Siêu Nhanh',
        feature_fast_desc: 'Tải xuống video chất lượng cao chỉ trong vài giây',
        feature_quality: 'Chất Lượng Cao',
        feature_quality_desc: 'Hỗ trợ tải video HD, Full HD, 4K và âm thanh 320kbps',
        feature_free: 'Miễn Phí',
        feature_free_desc: 'Hoàn toàn miễn phí, không cần đăng ký tài khoản',
        feature_safe: 'An Toàn',
        feature_safe_desc: 'Không lưu trữ video, bảo mật thông tin người dùng',
        
        // Steps
        step_1_title: 'Sao Chép Link',
        step_1_desc: 'Mở YouTube hoặc TikTok, sao chép link video bạn muốn tải.',
        step_2_title: 'Dán Link',
        step_2_desc: 'Dán link vào ô nhập liệu trên trang web của chúng tôi.',
        step_3_title: 'Tải Xuống',
        step_3_desc: 'Chọn định dạng (MP4/MP3) và chất lượng mong muốn, sau đó nhấn nút Tải Xuống.',
        
        // Quick Guide
        qg_title: 'Hướng dẫn nhanh',
        
        // FAQ
        faq_title: 'Câu hỏi thường gặp',
        faq_1_q: 'Tải video có mất phí không?',
        faq_1_a: 'Hoàn toàn miễn phí và không giới hạn lượt tải.',
        faq_2_q: 'Chất lượng video tải về như thế nào?',
        faq_2_a: 'Hỗ trợ đầy đủ các chất lượng từ 360p đến 4K tùy video gốc.',
        faq_3_q: 'Có cần đăng ký tài khoản không?',
        faq_3_a: 'Không cần đăng ký, sử dụng ngay lập tức.',
        
        // SEO Content
        about_downloader_pro_title: '📖 Về Downloader Pro',
        about_title: 'Công cụ tải video tốt nhất 2026',
        about_desc: 'Downloader Pro',
        about_desc_text: 'hỗ trợ tải video TikTok không logo, YouTube Full HD/4K và chuyển đổi MP3 chất lượng cao. Miễn phí, không quảng cáo, không cần đăng ký.',
        main_features_title: 'Tính năng chính',
        feat_tiktok_seo: '✅ TikTok: Tải video không logo, tải trọn bộ album ảnh, âm thanh MP3.',
        feat_youtube_seo: '✅ YouTube: Tải video 1080p, 4K, chuyển đổi MP3 320kbps.',
        feat_platform_seo: '✅ Đa nền tảng: Hoạt động mượt mà trên iPhone, Android, PC, Tablet.',
        feat_secure_seo: '✅ An toàn: Không lưu trữ video hay thông tin người dùng.',
        quick_guide_title: 'Hướng dẫn nhanh',
        qg_1: '1. Sao chép link: Lấy link video từ nút Chia sẻ trên ứng dụng TikTok/YouTube.',
        qg_2: '2. Dán link: Dán vào ô nhập liệu bên trên.',
        qg_3: '3. Tải xuống: Chọn định dạng MP4/MP3 và nhấn Tải về.',
        faq_2_q_alt: 'File tải về lưu ở đâu?',
        faq_2_a_alt: 'File sẽ nằm trong thư mục "Downloads" hoặc "Tệp" trên điện thoại/máy tính của bạn.',
        faq_3_q_alt: 'Tại sao không tải được?',
        faq_3_a_alt: 'Kiểm tra xem video có ở chế độ Riêng tư (Private) không. Chúng tôi chỉ hỗ trợ tải video Công khai (Public).',
        legal_note: 'Lưu ý:',
        legal_note_text: 'Công cụ chỉ dùng cho mục đích cá nhân. Vui lòng tôn trọng bản quyền tác giả.',
        
        // FAQ Section
        faq_section_title: '❓ Câu Hỏi Thường Gặp',
        faq_q1: 'Công cụ này có an toàn không?',
        faq_a1: 'Chúng tôi cam kết bảo mật thông tin người dùng và không cài đặt bất kỳ phần mềm độc hại nào.',
        faq_q2: 'Tại sao không tải được video?',
        faq_a2: 'Vui lòng kiểm tra lại liên kết (phải là công khai) hoặc thử lại sau vài phút nếu server đang bận.',
        faq_q3: 'Có giới hạn số lượng tải không?',
        faq_a3: 'Miễn phí 2 lượt/tuần. Nâng cấp Premium để tải không giới hạn.',
        
        // Guide Section
        guide_title: '🚀 Hướng Dẫn Sử Dụng',
        
        // Blog Section
        blog_section_title: '📚 Hướng Dẫn Chi Tiết',
        blog_desc: 'Khám phá các bài viết hướng dẫn chi tiết về cách tải video YouTube, TikTok',
        blog_youtube_title: 'Tải Video YouTube',
        blog_youtube_desc: 'Hướng dẫn chi tiết cách tải video YouTube về máy tính, điện thoại với chất lượng HD, Full HD, 4K',
        blog_tiktok_title: 'Tải TikTok Không Logo',
        blog_tiktok_desc: 'Cách tải video TikTok không có logo watermark, tải album ảnh slideshow chất lượng gốc',
        blog_mp3_title: 'Chuyển YouTube Sang MP3',
        blog_mp3_desc: 'Hướng dẫn chuyển đổi video YouTube sang file MP3 với chất lượng 128kbps, 192kbps, 320kbps',
        blog_read_more: 'Đọc thêm →',
        
        // Promo Section
        promo_tiktok_title: '🎉 Tải TikTok Không Logo!',
        promo_tiktok_desc: 'Video chất lượng cao, không dính watermark. Hoàn toàn miễn phí!',
        
        // Footer
        footer_rights: '© 2026 Downloader Pro. All rights reserved.',
        
        // Donate
        donate_title: 'Ủng hộ duy trì website',
        donate_subtitle: 'Nếu bạn thấy website hữu ích, hãy ủng hộ chúng tôi một ly cà phê để duy trì và phát triển thêm nhiều tính năng mới!',
        donate_amount: 'Chọn số tiền:',
        donate_custom: 'Khác',
        donate_name: 'Tên của bạn (tùy chọn):',
        donate_message: 'Lời nhắn (tùy chọn):',
        donate_button: '💝 Ủng hộ ngay',
        donate_messages_title: '💬 Lời nhắn từ những người ủng hộ',
        donate_messages_subtitle: 'Cảm ơn sự hỗ trợ của các bạn!',
        
        // Footer
        footer_desc: 'Công cụ tải video YouTube, TikTok miễn phí tốt nhất Việt Nam. Hỗ trợ chuyển đổi MP4, MP3 chất lượng cao.',
        footer_contact: 'Liên hệ hỗ trợ',
        footer_dev_info: 'Phát triển bởi đội ngũ kỹ sư Việt Nam',
        
        // Statistics
        stats_title: '📊 THỐNG KÊ TRUY CẬP',
        stats_online: 'Đang online:',
        stats_today: 'Hôm nay:',
        stats_monthly: 'Trong tháng:',
        stats_total: 'Tổng pageview:',
        
        // Download limit messages
        limit_title: '⚠️ Đã hết lượt tải miễn phí',
        limit_message: 'Bạn đã sử dụng hết 2 lượt tải miễn phí trong tháng này.',
        limit_explanation: 'Để duy trì và phát triển website, chúng tôi cần chi phí cho server, băng thông và bảo trì. Mong bạn thông cảm!',
        limit_premium_title: '✨ Nâng cấp Premium',
        limit_premium_benefits: '• Tải xuống không giới hạn trong 30 ngày\n• Không quảng cáo\n• Ưu tiên hỗ trợ',
        limit_amount_label: 'Chọn hoặc nhập số tiền:',
        limit_amount_custom: 'Số tiền khác',
        limit_name_label: 'Tên của bạn (tùy chọn):',
        limit_button_pay: '💳 Thanh toán',
        limit_button_cancel: 'Để sau',
        premium_status: 'Premium đến',
        downloads_remaining: 'Còn {count} lượt tải',
        
        // Require login modal
        require_login_title: 'Yêu cầu đăng nhập',
        require_login_message: 'Vui lòng đăng nhập để tải xuống. Đăng ký miễn phí để nhận 2 lượt tải mỗi tháng!',
        require_login_btn: '🔑 Đăng nhập ngay',
        require_register_btn: '📝 Đăng ký miễn phí',
        limit_reached_title: 'Hết lượt tải miễn phí!',
        limit_reached_message: '🚫 Bạn đã hết 2 lượt tải miễn phí trong tháng này. Vui lòng mua Premium để tải không giới hạn!',
        upgrade_premium_btn: '👑 Mua Premium - Tải không giới hạn',
        register_premium_btn: '📝 Đăng ký & Nâng cấp Premium',
        close_btn: 'Đóng',
        
        // Donation Promo Modal
        promo_title: 'Ủng hộ duy trì website',
        promo_message: 'Bạn vừa tải thành công! 🎉',
        promo_explanation: 'Nếu thấy hữu ích, hãy ủng hộ chúng tôi một ly cà phê để duy trì server và phát triển thêm tính năng mới.',
        promo_benefits_title: 'Sự ủng hộ của bạn giúp:',
        promo_benefit_1: 'Duy trì server 24/7',
        promo_benefit_2: 'Phát triển tính năng mới',
        promo_benefit_3: 'Giữ website miễn phí cho mọi người',
        promo_skip: 'Bỏ qua',
        promo_donate: '💝 Ủng hộ',
        promo_custom_amount: 'Hoặc nhập số tiền khác:',
        promo_amount_placeholder: 'Nhập số tiền (VND)',
        promo_name_label: 'Tên của bạn:',
        promo_name_placeholder: 'Nhập tên để hiển thị...',
        promo_message_label: 'Lời nhắn (tùy chọn):',
        promo_message_placeholder: 'Viết lời nhắn để hiển thị trong phần ủng hộ...',
        
        // Auth Pages
        auth_login_title: 'Đăng nhập',
        auth_login_subtitle: 'Đăng nhập để trải nghiệm đầy đủ tính năng',
        auth_login_welcome: 'Chào mừng bạn quay lại với chúng tôi!',
        auth_register_title: 'Đăng ký tài khoản',
        auth_register_subtitle: 'Bắt đầu trải nghiệm các tính năng Premium!',
        auth_forgot_title: 'Quên mật khẩu',
        auth_forgot_subtitle: 'Nhập email để nhận mã khôi phục',
        auth_username: 'Tên đăng nhập',
        auth_email: 'Địa chỉ Email',
        auth_password: 'Mật khẩu',
        auth_confirm_password: 'Xác nhận lại mật khẩu',
        auth_otp_code: 'Mã OTP',
        auth_btn_login: 'Đăng nhập',
        auth_btn_register: 'Đăng ký',
        auth_btn_send_otp: 'Gửi mã OTP',
        auth_btn_verify: 'Xác thực',
        auth_btn_reset: 'Đặt lại mật khẩu',
        auth_or_continue: 'Hoặc tiếp tục với',
        auth_google_login: 'Đăng nhập với Google',
        auth_have_account: 'Đã có tài khoản?',
        auth_no_account: 'Chưa có tài khoản?',
        auth_forgot_password: 'Quên mật khẩu?',
        auth_back_to_login: 'Quay lại đăng nhập',
        auth_login_id: 'Tài khoản hoặc Email',
        auth_login_id_placeholder: 'Nhập username hoặc email',
        auth_password_placeholder: 'Nhập mật khẩu',
        auth_otp_sent: 'Mã OTP đã được gửi đến email:',
        auth_otp_enter: 'Nhập mã OTP (6 chữ số)',
        auth_btn_verify_email: 'Xác Thực Email',
        auth_resend_otp: 'Gửi lại mã OTP',
        auth_processing: 'Đang xử lý...',
        auth_username_placeholder: 'vd: myusername',
        auth_username_hint: '3-30 ký tự, chữ thường, số và dấu _',
        auth_email_placeholder: 'example@email.com',
        auth_password_min: 'Tối thiểu 6 ký tự',
        auth_confirm_password_placeholder: 'Nhập lại mật khẩu',
        auth_btn_create_account: 'Tạo Tài Khoản',
        auth_registering: 'Đang đăng ký...',
        auth_otp_sent_register: 'Mã OTP đã được gửi đến email của bạn:',
        auth_otp_enter_6: 'Nhập mã xác thực (6 số)',
        auth_btn_verify_account: 'Xác Thực Tài Khoản',
        auth_resend_code: 'Gửi lại mã xác thực',
        auth_login_here: 'Đăng nhập tại đây',
        auth_create_account: 'Tạo tài khoản mới',
        
        // Account Page
        account_title: 'Quản lý tài khoản',
        account_subtitle: 'Xem thông tin chi tiết và quản lý gói Premium',
        account_profile: 'Thông tin cá nhân',
        account_premium_status: 'Trạng thái Premium',
        account_downloads: 'Lượt tải xuống',
        account_settings: 'Cài đặt',
        account_username: 'Tên đăng nhập',
        account_email: 'Địa chỉ email',
        account_member_since: 'Thành viên từ',
        account_account_type: 'Loại tài khoản',
        account_free: 'Miễn phí',
        account_premium: 'Premium',
        account_premium_active: 'Premium đang hoạt động',
        account_premium_expires: 'Hết hạn vào',
        account_days_left: 'Còn lại',
        account_days: 'ngày',
        account_downloads_month: 'Lượt tải tháng này',
        account_downloads_total: 'Tổng lượt tải',
        account_downloads_limit: 'Giới hạn',
        account_downloads_unlimited: 'Không giới hạn',
        account_downloads_remaining: 'Còn lại',
        account_premium_benefits: 'Đặc quyền Premium',
        account_benefit_unlimited: 'Tải video không giới hạn',
        account_benefit_no_ads: 'Không có quảng cáo',
        account_benefit_priority: 'Tốc độ tải tối đa',
        account_benefit_support: 'Hỗ trợ ưu tiên',
        account_benefit_features: 'Truy cập tính năng mới sớm',
        account_upgrade_premium: 'Nâng cấp Premium',
        account_renew_premium: 'Gia hạn Premium',
        account_payment_title: 'Thanh toán Premium',
        account_payment_subtitle: 'Ủng hộ bất kỳ số tiền nào để nhận 30 ngày Premium',
        account_amount_popular: 'PHỔ BIẾN',
        account_amount_custom: 'Hoặc nhập số tiền khác',
        account_amount_min: 'tối thiểu',
        account_btn_pay: 'Thanh toán ngay',
        account_btn_home: 'Trang chủ',
        account_btn_logout: 'Đăng xuất',
        account_speed: 'Tốc độ tải',
        account_speed_max: 'Tối đa (Ưu tiên)',
        account_speed_standard: 'Tiêu chuẩn',
        account_ads: 'Quảng cáo',
        account_ads_off: 'Đã tắt hoàn toàn',
        account_ads_shown: 'Có hiển thị',
        account_download_limit: 'Giới hạn tải xuống',
        account_used: 'Đã sử dụng',
        account_times: 'lượt',
        account_remaining: 'Còn',
        account_no_downloads: 'Đã hết lượt',
        account_refresh_date: 'Làm mới vào',
        account_next_month: 'Đầu tháng sau',
        premium_success_title: 'Cảm ơn bạn rất nhiều!',
        premium_success_message: 'Giao dịch thành công. Tài khoản Premium đã được kích hoạt.',
        premium_success_support: 'Sự ủng hộ của bạn giúp chúng tôi phát triển Downloader Pro tốt hơn!',
        premium_success_btn: 'Bắt đầu trải nghiệm',
        
        // Premium Page
        nav_premium: 'Premium',
        premium_page_title: 'Nâng Cấp Premium',
        premium_page_subtitle: 'Trải nghiệm đầy đủ tính năng không giới hạn',
        premium_benefits_title: 'Đặc Quyền Premium',
        premium_member_badge: '⭐ Premium Member',
        premium_free_badge: '🆓 Free Member',
        premium_expires: 'Hết hạn',
        premium_days_left: 'Còn',
        premium_days: 'ngày',
        premium_free_downloads_week: 'Lượt tải miễn phí tháng này',
        premium_start_date: 'Bắt đầu',
        premium_amount: 'Số tiền',
        premium_status: 'Trạng thái',
        premium_active: '✓ Đang hoạt động',
        premium_benefit_unlimited_desc: 'Tải video không giới hạn mỗi tháng',
        premium_benefit_no_ads_desc: 'Trải nghiệm mượt mà, không bị làm phiền',
        premium_benefit_priority_desc: 'Ưu tiên xử lý, tải nhanh hơn',
        premium_benefit_support_desc: 'Được hỗ trợ nhanh chóng khi cần',
        premium_processing: 'Đang xử lý...'
    },
    en: {
        // Navigation
        nav_home: 'Home',
        nav_news: 'News',
        nav_blog: 'Blog',
        nav_mode: 'Mode',
        nav_account: 'Account',
        nav_login: 'Login',
        nav_logout: 'Logout',
        lang_name: 'English',
        donate_header: 'Donate',
        
        // Hero Section
        hero_title_prefix: 'Download Videos',
        hero_title_suffix: 'Fast & Easy',
        hero_subtitle: 'Convert videos from YouTube & TikTok to MP4, MP3 high quality - Free & Unlimited',
        stats_downloads: 'downloads processed',
        
        // Tabs
        tab_youtube: 'YouTube',
        tab_youtube_hint: 'Download videos & music from YouTube',
        tab_tiktok: 'TikTok',
        tab_tiktok_hint: 'Download videos & photos from TikTok',
        
        // Cards
        card_title_youtube: 'Download YouTube Video',
        card_desc_youtube: 'Paste YouTube video link to download',
        card_title_tiktok: 'Download TikTok Video',
        card_desc_tiktok: 'Paste TikTok video link to download',
        
        // Input & Buttons
        input_placeholder_youtube: 'Paste YouTube link here...',
        input_placeholder_tiktok: 'Paste TikTok link here...',
        btn_paste: 'Paste',
        btn_download: 'Download',
        btn_download_again: 'Download Again',
        
        // Quality & Format
        quality_label: 'Choose format:',
        format_video: 'Video',
        format_audio: 'Audio',
        quality_best: 'Best',
        quality_high: 'High',
        quality_medium: 'Medium',
        
        // Gallery
        select_images_prompt: 'Select images to download:',
        select_all: 'Select All',
        deselect_all: 'Deselect All',
        
        // Progress
        progress_preparing: 'Preparing...',
        progress_downloading: 'Downloading...',
        progress_processing: 'Processing...',
        progress_completed: 'Completed!',
        download_complete: '✅ Download complete! File is being saved...',
        
        // Features
        feature_fast: 'Super Fast',
        feature_fast_desc: 'Download high quality videos in just seconds',
        feature_quality: 'High Quality',
        feature_quality_desc: 'Support HD, Full HD, 4K video and 320kbps audio',
        feature_free: 'Free',
        feature_free_desc: 'Completely free, no account registration required',
        feature_safe: 'Safe',
        feature_safe_desc: 'No video storage, user information security',
        
        // Steps
        step_1_title: 'Copy Link',
        step_1_desc: 'Open YouTube or TikTok, copy the video link you want to download.',
        step_2_title: 'Paste Link',
        step_2_desc: 'Paste the link into the input field on our website.',
        step_3_title: 'Download',
        step_3_desc: 'Choose format (MP4/MP3) and desired quality, then click Download button.',
        
        // Quick Guide
        qg_title: 'Quick Guide',
        
        // FAQ
        faq_title: 'Frequently Asked Questions',
        faq_1_q: 'Is video download free?',
        faq_1_a: 'Completely free with unlimited downloads.',
        faq_2_q: 'What is the video quality?',
        faq_2_a: 'Support all qualities from 360p to 4K depending on original video.',
        faq_3_q: 'Do I need to register an account?',
        faq_3_a: 'No registration required, use immediately.',
        
        // SEO Content
        about_downloader_pro_title: '📖 About Downloader Pro',
        about_title: 'Best Video Downloader Tool 2026',
        about_desc: 'Downloader Pro',
        about_desc_text: 'supports downloading TikTok videos without watermark, YouTube Full HD/4K and high quality MP3 conversion. Free, no ads, no registration required.',
        main_features_title: 'Main Features',
        feat_tiktok_seo: '✅ TikTok: Download videos without watermark, download full photo albums, MP3 audio.',
        feat_youtube_seo: '✅ YouTube: Download 1080p, 4K videos, convert to 320kbps MP3.',
        feat_platform_seo: '✅ Cross-platform: Works smoothly on iPhone, Android, PC, Tablet.',
        feat_secure_seo: '✅ Secure: No video storage or user information.',
        quick_guide_title: 'Quick Guide',
        qg_1: '1. Copy link: Get video link from Share button on TikTok/YouTube app.',
        qg_2: '2. Paste link: Paste into the input field above.',
        qg_3: '3. Download: Choose MP4/MP3 format and click Download.',
        faq_2_q_alt: 'Where is the downloaded file saved?',
        faq_2_a_alt: 'The file will be in the "Downloads" or "Files" folder on your phone/computer.',
        faq_3_q_alt: 'Why can\'t I download?',
        faq_3_a_alt: 'Check if the video is in Private mode. We only support downloading Public videos.',
        legal_note: 'Note:',
        legal_note_text: 'This tool is for personal use only. Please respect copyright.',
        
        // FAQ Section
        faq_section_title: '❓ Frequently Asked Questions',
        faq_q1: 'Is this tool safe?',
        faq_a1: 'We are committed to protecting user information and do not install any malware.',
        faq_q2: 'Why can\'t I download videos?',
        faq_a2: 'Please check the link (must be public) or try again in a few minutes if the server is busy.',
        faq_q3: 'Is there a download limit?',
        faq_a3: 'Free 2 downloads/week. Upgrade to Premium for unlimited downloads.',
        
        // Guide Section
        guide_title: '🚀 How to Use',
        
        // Blog Section
        blog_section_title: '📚 Detailed Guides',
        blog_desc: 'Explore detailed guides on how to download YouTube, TikTok videos',
        blog_youtube_title: 'Download YouTube Videos',
        blog_youtube_desc: 'Detailed guide on how to download YouTube videos to computer, phone in HD, Full HD, 4K quality',
        blog_tiktok_title: 'Download TikTok Without Watermark',
        blog_tiktok_desc: 'How to download TikTok videos without watermark logo, download original quality photo slideshow albums',
        blog_mp3_title: 'Convert YouTube to MP3',
        blog_mp3_desc: 'Guide to convert YouTube videos to high quality 320kbps MP3 music files',
        blog_read_more: 'Read more →',
        
        // Promo Section
        promo_tiktok_title: '🎉 Download TikTok Without Watermark!',
        promo_tiktok_desc: 'High quality videos, no watermark. Completely free!',
        
        // Footer
        footer_rights: '© 2026 Downloader Pro. All rights reserved.',
        
        // Donate
        donate_title: 'Support Our Website',
        donate_subtitle: 'If you find our website useful, please support us with a coffee to maintain and develop more new features!',
        donate_amount: 'Choose amount:',
        donate_custom: 'Custom',
        donate_name: 'Your name (optional):',
        donate_message: 'Message (optional):',
        donate_button: '💝 Donate Now',
        donate_messages_title: '💬 Messages from Supporters',
        donate_messages_subtitle: 'Thank you for your support!',
        
        // Footer
        footer_desc: 'Best free YouTube, TikTok video downloader in Vietnam. Support high quality MP4, MP3 conversion.',
        footer_contact: 'Contact Support',
        footer_dev_info: 'Developed by Vietnamese Engineers Team',
        
        // Statistics
        stats_title: '📊 ACCESS STATISTICS',
        stats_online: 'Online now:',
        stats_today: 'Today:',
        stats_monthly: 'This month:',
        stats_total: 'Total pageviews:',
        
        // Download limit messages
        limit_title: '⚠️ Free Downloads Limit Reached',
        limit_message: 'You have used all 2 free downloads this month.',
        limit_explanation: 'To maintain and develop the website, we need costs for servers, bandwidth and maintenance. Thank you for understanding!',
        limit_premium_title: '✨ Upgrade to Premium',
        limit_premium_benefits: '• Unlimited downloads for 30 days\n• No ads\n• Priority support',
        limit_amount_label: 'Choose or enter amount:',
        limit_amount_custom: 'Custom amount',
        limit_name_label: 'Your name (optional):',
        limit_button_pay: '💳 Pay Now',
        limit_button_cancel: 'Later',
        premium_status: 'Premium until',
        downloads_remaining: '{count} downloads left',
        
        // Require login modal
        require_login_title: 'Login Required',
        require_login_message: 'Please login to download. Sign up for free to get 2 downloads per month!',
        require_login_btn: '🔑 Login Now',
        require_register_btn: '📝 Sign Up Free',
        limit_reached_title: 'Free Downloads Limit Reached!',
        limit_reached_message: '🚫 You have used all 2 free downloads this month. Please purchase Premium for unlimited downloads!',
        upgrade_premium_btn: '👑 Purchase Premium - Unlimited Downloads',
        register_premium_btn: '📝 Sign Up & Upgrade Premium',
        close_btn: 'Close',
        
        // Donation Promo Modal
        promo_title: 'Support Our Website',
        promo_message: 'Download successful! 🎉',
        promo_explanation: 'If you find it useful, please support us with a coffee to maintain servers and develop new features.',
        promo_benefits_title: 'Your support helps:',
        promo_benefit_1: 'Keep servers running 24/7',
        promo_benefit_2: 'Develop new features',
        promo_benefit_3: 'Keep website free for everyone',
        promo_skip: 'Skip',
        promo_donate: '💝 Donate',
        promo_custom_amount: 'Or enter custom amount:',
        promo_amount_placeholder: 'Enter amount (VND)',
        promo_name_label: 'Your name:',
        promo_name_placeholder: 'Enter name to display...',
        promo_message_label: 'Message (optional):',
        promo_message_placeholder: 'Write a message to display in supporters section...',
        
        // Auth Pages
        auth_login_title: 'Login',
        auth_login_subtitle: 'Login to access full features',
        auth_login_welcome: 'Welcome back!',
        auth_register_title: 'Create Account',
        auth_register_subtitle: 'Start experiencing Premium features!',
        auth_forgot_title: 'Forgot Password',
        auth_forgot_subtitle: 'Enter your email to receive recovery code',
        auth_username: 'Username',
        auth_email: 'Email Address',
        auth_password: 'Password',
        auth_confirm_password: 'Confirm Password',
        auth_otp_code: 'OTP Code',
        auth_btn_login: 'Login',
        auth_btn_register: 'Register',
        auth_btn_send_otp: 'Send OTP',
        auth_btn_verify: 'Verify',
        auth_btn_reset: 'Reset Password',
        auth_or_continue: 'Or continue with',
        auth_google_login: 'Login with Google',
        auth_have_account: 'Already have an account?',
        auth_no_account: "Don't have an account?",
        auth_forgot_password: 'Forgot password?',
        auth_back_to_login: 'Back to login',
        auth_login_id: 'Username or Email',
        auth_login_id_placeholder: 'Enter username or email',
        auth_password_placeholder: 'Enter password',
        auth_otp_sent: 'OTP code has been sent to email:',
        auth_otp_enter: 'Enter OTP code (6 digits)',
        auth_btn_verify_email: 'Verify Email',
        auth_resend_otp: 'Resend OTP',
        auth_processing: 'Processing...',
        auth_username_placeholder: 'e.g: myusername',
        auth_username_hint: '3-30 characters, lowercase, numbers and _',
        auth_email_placeholder: 'example@email.com',
        auth_password_min: 'Minimum 6 characters',
        auth_confirm_password_placeholder: 'Re-enter password',
        auth_btn_create_account: 'Create Account',
        auth_registering: 'Registering...',
        auth_otp_sent_register: 'OTP code has been sent to your email:',
        auth_otp_enter_6: 'Enter verification code (6 digits)',
        auth_btn_verify_account: 'Verify Account',
        auth_resend_code: 'Resend verification code',
        auth_login_here: 'Login here',
        auth_create_account: 'Create new account',
        
        // Account Page
        account_title: 'Account Management',
        account_subtitle: 'View details and manage your Premium subscription',
        account_profile: 'Profile Information',
        account_premium_status: 'Premium Status',
        account_downloads: 'Downloads',
        account_settings: 'Settings',
        account_username: 'Username',
        account_email: 'Email Address',
        account_member_since: 'Member Since',
        account_account_type: 'Account Type',
        account_free: 'Free',
        account_premium: 'Premium',
        account_premium_active: 'Premium Active',
        account_premium_expires: 'Expires on',
        account_days_left: 'Remaining',
        account_days: 'days',
        account_downloads_month: 'Downloads This Month',
        account_downloads_total: 'Total Downloads',
        account_downloads_limit: 'Limit',
        account_downloads_unlimited: 'Unlimited',
        account_downloads_remaining: 'Remaining',
        account_premium_benefits: 'Premium Benefits',
        account_benefit_unlimited: 'Unlimited video downloads',
        account_benefit_no_ads: 'No advertisements',
        account_benefit_priority: 'Maximum download speed',
        account_benefit_support: 'Priority support',
        account_benefit_features: 'Early access to new features',
        account_upgrade_premium: 'Upgrade to Premium',
        account_renew_premium: 'Renew Premium',
        account_payment_title: 'Premium Payment',
        account_payment_subtitle: 'Support any amount to get 30 days Premium',
        account_amount_popular: 'POPULAR',
        account_amount_custom: 'Or enter custom amount',
        account_amount_min: 'minimum',
        account_btn_pay: 'Pay Now',
        account_btn_home: 'Home',
        account_btn_logout: 'Logout',
        account_speed: 'Download Speed',
        account_speed_max: 'Maximum (Priority)',
        account_speed_standard: 'Standard',
        account_ads: 'Advertisements',
        account_ads_off: 'Completely disabled',
        account_ads_shown: 'Displayed',
        account_download_limit: 'Download Limit',
        account_used: 'Used',
        account_times: 'times',
        account_remaining: 'Remaining',
        account_no_downloads: 'No downloads left',
        account_refresh_date: 'Refreshes on',
        account_next_month: 'Beginning of next month',
        premium_success_title: 'Thank You So Much!',
        premium_success_message: 'Transaction successful. Premium account has been activated.',
        premium_success_support: 'Your support helps us develop Downloader Pro better!',
        premium_success_btn: 'Start Experience',
        
        // Premium Page
        nav_premium: 'Premium',
        premium_page_title: 'Upgrade to Premium',
        premium_page_subtitle: 'Experience full features without limits',
        premium_benefits_title: 'Premium Benefits',
        premium_member_badge: '⭐ Premium Member',
        premium_free_badge: '🆓 Free Member',
        premium_expires: 'Expires',
        premium_days_left: 'Remaining',
        premium_days: 'days',
        premium_free_downloads_week: 'Free downloads this month',
        premium_start_date: 'Start Date',
        premium_amount: 'Amount',
        premium_status: 'Status',
        premium_active: '✓ Active',
        premium_benefit_unlimited_desc: 'Unlimited video downloads per month',
        premium_benefit_no_ads_desc: 'Smooth experience, no interruptions',
        premium_benefit_priority_desc: 'Priority processing, faster downloads',
        premium_benefit_support_desc: 'Quick support when needed',
        premium_processing: 'Processing...'
    },
    ru: {
        // Navigation
        nav_home: 'Главная',
        nav_news: 'Новости',
        nav_blog: 'Блог',
        nav_mode: 'Режим',
        nav_account: 'Аккаунт',
        nav_login: 'Вход',
        nav_logout: 'Выход',
        lang_name: 'Русский',
        donate_header: 'Поддержать',
        
        // Hero Section
        hero_title_prefix: 'Скачать Видео',
        hero_title_suffix: 'Быстро и Легко',
        hero_subtitle: 'Конвертируйте видео из YouTube и TikTok в MP4, MP3 высокого качества - Бесплатно и Без ограничений',
        stats_downloads: 'загрузок обработано',
        
        // Tabs
        tab_youtube: 'YouTube',
        tab_youtube_hint: 'Скачать видео и музыку с YouTube',
        tab_tiktok: 'TikTok',
        tab_tiktok_hint: 'Скачать видео и фото с TikTok',
        
        // Cards
        card_title_youtube: 'Скачать Видео YouTube',
        card_desc_youtube: 'Вставьте ссылку на видео YouTube для загрузки',
        card_title_tiktok: 'Скачать Видео TikTok',
        card_desc_tiktok: 'Вставьте ссылку на видео TikTok для загрузки',
        
        // Input & Buttons
        input_placeholder_youtube: 'Вставьте ссылку YouTube здесь...',
        input_placeholder_tiktok: 'Вставьте ссылку TikTok здесь...',
        btn_paste: 'Вставить',
        btn_download: 'Скачать',
        btn_download_again: 'Скачать Снова',
        
        // Quality & Format
        quality_label: 'Выберите формат:',
        format_video: 'Видео',
        format_audio: 'Аудио',
        quality_best: 'Лучшее',
        quality_high: 'Высокое',
        quality_medium: 'Среднее',
        
        // Gallery
        select_images_prompt: 'Выберите изображения для загрузки:',
        select_all: 'Выбрать все',
        deselect_all: 'Снять выбор',
        
        // Progress
        progress_preparing: 'Подготовка...',
        progress_downloading: 'Загрузка...',
        progress_processing: 'Обработка...',
        progress_completed: 'Завершено!',
        download_complete: '✅ Загрузка завершена! Файл сохраняется...',
        
        // Features
        feature_fast: 'Супер Быстро',
        feature_fast_desc: 'Загружайте видео высокого качества за считанные секунды',
        feature_quality: 'Высокое Качество',
        feature_quality_desc: 'Поддержка HD, Full HD, 4K видео и 320kbps аудио',
        feature_free: 'Бесплатно',
        feature_free_desc: 'Полностью бесплатно, регистрация не требуется',
        feature_safe: 'Безопасно',
        feature_safe_desc: 'Без хранения видео, безопасность информации пользователя',
        
        // Steps
        step_1_title: 'Скопировать Ссылку',
        step_1_desc: 'Откройте YouTube или TikTok, скопируйте ссылку на видео, которое хотите загрузить.',
        step_2_title: 'Вставить Ссылку',
        step_2_desc: 'Вставьте ссылку в поле ввода на нашем сайте.',
        step_3_title: 'Скачать',
        step_3_desc: 'Выберите формат (MP4/MP3) и желаемое качество, затем нажмите кнопку Скачать.',
        
        // Quick Guide
        qg_title: 'Краткое Руководство',
        
        // FAQ
        faq_title: 'Часто Задаваемые Вопросы',
        faq_1_q: 'Загрузка видео бесплатна?',
        faq_1_a: 'Полностью бесплатно с неограниченными загрузками.',
        faq_2_q: 'Какое качество видео?',
        faq_2_a: 'Поддержка всех качеств от 360p до 4K в зависимости от оригинального видео.',
        faq_3_q: 'Нужна ли регистрация аккаунта?',
        faq_3_a: 'Регистрация не требуется, используйте сразу.',
        
        // SEO Content
        about_downloader_pro_title: '📖 О Downloader Pro',
        about_title: 'Лучший инструмент для загрузки видео 2026',
        about_desc: 'Downloader Pro',
        about_desc_text: 'поддерживает загрузку видео TikTok без водяного знака, YouTube Full HD/4K и высококачественное преобразование MP3. Бесплатно, без рекламы, без регистрации.',
        main_features_title: 'Основные функции',
        feat_tiktok_seo: '✅ TikTok: Загрузка видео без водяного знака, загрузка полных фотоальбомов, аудио MP3.',
        feat_youtube_seo: '✅ YouTube: Загрузка видео 1080p, 4K, конвертация в MP3 320kbps.',
        feat_platform_seo: '✅ Кроссплатформенность: Работает на iPhone, Android, ПК, планшетах.',
        feat_secure_seo: '✅ Безопасность: Без хранения видео или информации пользователя.',
        quick_guide_title: 'Краткое руководство',
        qg_1: '1. Скопировать ссылку: Получите ссылку на видео из кнопки "Поделиться" в приложении TikTok/YouTube.',
        qg_2: '2. Вставить ссылку: Вставьте в поле ввода выше.',
        qg_3: '3. Скачать: Выберите формат MP4/MP3 и нажмите "Скачать".',
        faq_2_q_alt: 'Где сохраняется загруженный файл?',
        faq_2_a_alt: 'Файл будет в папке "Загрузки" или "Файлы" на вашем телефоне/компьютере.',
        faq_3_q_alt: 'Почему не могу скачать?',
        faq_3_a_alt: 'Проверьте, не находится ли видео в режиме "Приватное". Мы поддерживаем только публичные видео.',
        legal_note: 'Примечание:',
        legal_note_text: 'Этот инструмент предназначен только для личного использования. Пожалуйста, уважайте авторские права.',
        
        // FAQ Section
        faq_section_title: '❓ Часто Задаваемые Вопросы',
        faq_q1: 'Безопасен ли этот инструмент?',
        faq_a1: 'Мы обязуемся защищать информацию пользователей и не устанавливаем вредоносное ПО.',
        faq_q2: 'Почему не могу скачать видео?',
        faq_a2: 'Проверьте ссылку (должна быть публичной) или попробуйте снова через несколько минут, если сервер занят.',
        faq_q3: 'Есть ли ограничение на загрузки?',
        faq_a3: 'Бесплатно 2 загрузки/неделю. Обновитесь до Premium для неограниченных загрузок.',
        
        // Guide Section
        guide_title: '🚀 Как использовать',
        
        // Blog Section
        blog_section_title: '📚 Подробные руководства',
        blog_desc: 'Изучите подробные руководства по загрузке видео YouTube, TikTok',
        blog_youtube_title: 'Скачать видео YouTube',
        blog_youtube_desc: 'Подробное руководство по загрузке видео YouTube на компьютер, телефон в качестве HD, Full HD, 4K',
        blog_tiktok_title: 'Скачать TikTok без водяного знака',
        blog_tiktok_desc: 'Как скачать видео TikTok без водяного знака, загрузить фотоальбомы слайд-шоу в оригинальном качестве',
        blog_mp3_title: 'Конвертировать YouTube в MP3',
        blog_mp3_desc: 'Руководство по конвертации видео YouTube в высококачественные музыкальные файлы MP3 320kbps',
        blog_read_more: 'Читать далее →',
        
        // Promo Section
        promo_tiktok_title: '🎉 Скачать TikTok без водяного знака!',
        promo_tiktok_desc: 'Видео высокого качества, без водяного знака. Совершенно бесплатно!',
        
        // Footer
        footer_rights: '© 2026 Downloader Pro. Все права защищены.',
        
        // Donate
        donate_title: 'Поддержите наш сайт',
        donate_subtitle: 'Если вы находите наш сайт полезным, поддержите нас чашкой кофе, чтобы поддерживать и разрабатывать новые функции!',
        donate_amount: 'Выберите сумму:',
        donate_custom: 'Другое',
        donate_name: 'Ваше имя (необязательно):',
        donate_message: 'Сообщение (необязательно):',
        donate_button: '💝 Поддержать сейчас',
        donate_messages_title: '💬 Сообщения от спонсоров',
        donate_messages_subtitle: 'Спасибо за вашу поддержку!',
        
        // Footer
        footer_desc: 'Лучший бесплатный загрузчик видео YouTube, TikTok во Вьетнаме. Поддержка высококачественного преобразования MP4, MP3.',
        footer_contact: 'Связаться с поддержкой',
        footer_dev_info: 'Разработано командой вьетнамских инженеров',
        
        // Statistics
        stats_title: '📊 СТАТИСТИКА ПОСЕЩЕНИЙ',
        stats_online: 'Онлайн сейчас:',
        stats_today: 'Сегодня:',
        stats_monthly: 'В этом месяце:',
        stats_total: 'Всего просмотров:',
        
        // Download limit messages
        limit_title: '⚠️ Лимит бесплатных загрузок исчерпан',
        limit_message: 'Вы использовали все 2 бесплатные загрузки на этой неделе.',
        limit_explanation: 'Для поддержания и развития сайта нам нужны средства на серверы, трафик и обслуживание. Спасибо за понимание!',
        limit_premium_title: '✨ Обновить до Premium',
        limit_premium_benefits: '• Неограниченные загрузки на 30 дней\n• Без рекламы\n• Приоритетная поддержка',
        limit_amount_label: 'Выберите или введите сумму:',
        limit_amount_custom: 'Другая сумма',
        limit_name_label: 'Ваше имя (необязательно):',
        limit_button_pay: '💳 Оплатить',
        limit_button_cancel: 'Позже',
        premium_status: 'Premium до',
        downloads_remaining: 'Осталось {count} загрузок',
        
        // Require login modal
        require_login_title: 'Требуется вход',
        require_login_message: 'Пожалуйста, войдите, чтобы скачать. Зарегистрируйтесь бесплатно и получите 2 загрузки в неделю!',
        require_login_btn: '🔑 Войти сейчас',
        require_register_btn: '📝 Бесплатная регистрация',
        limit_reached_title: 'Лимит бесплатных загрузок исчерпан!',
        limit_reached_message: '🚫 Вы использовали все 2 бесплатные загрузки на этой неделе. Пожалуйста, купите Premium для неограниченных загрузок!',
        upgrade_premium_btn: '👑 Купить Premium - Неограниченные загрузки',
        register_premium_btn: '📝 Зарегистрироваться и обновить Premium',
        close_btn: 'Закрыть',
        
        // Donation Promo Modal
        promo_title: 'Поддержите наш сайт',
        promo_message: 'Загрузка успешна! 🎉',
        promo_explanation: 'Если вам полезно, поддержите нас чашкой кофе для поддержания серверов и разработки новых функций.',
        promo_benefits_title: 'Ваша поддержка помогает:',
        promo_benefit_1: 'Поддерживать серверы 24/7',
        promo_benefit_2: 'Разрабатывать новые функции',
        promo_benefit_3: 'Сохранять сайт бесплатным для всех',
        promo_skip: 'Пропустить',
        promo_donate: '💝 Поддержать',
        promo_custom_amount: 'Или введите другую сумму:',
        promo_amount_placeholder: 'Введите сумму (VND)',
        promo_name_label: 'Ваше имя:',
        promo_name_placeholder: 'Введите имя для отображения...',
        promo_message_label: 'Сообщение (необязательно):',
        promo_message_placeholder: 'Напишите сообщение для отображения в разделе поддержки...',
        
        // Auth Pages
        auth_login_title: 'Войти',
        auth_login_subtitle: 'Войдите для доступа ко всем функциям',
        auth_login_welcome: 'С возвращением!',
        auth_register_title: 'Создать аккаунт',
        auth_register_subtitle: 'Начните использовать Premium функции!',
        auth_forgot_title: 'Забыли пароль',
        auth_forgot_subtitle: 'Введите email для получения кода восстановления',
        auth_username: 'Имя пользователя',
        auth_email: 'Email адрес',
        auth_password: 'Пароль',
        auth_confirm_password: 'Подтвердите пароль',
        auth_otp_code: 'OTP код',
        auth_btn_login: 'Войти',
        auth_btn_register: 'Зарегистрироваться',
        auth_btn_send_otp: 'Отправить OTP',
        auth_btn_verify: 'Проверить',
        auth_btn_reset: 'Сбросить пароль',
        auth_or_continue: 'Или продолжить с',
        auth_google_login: 'Войти через Google',
        auth_have_account: 'Уже есть аккаунт?',
        auth_no_account: 'Нет аккаунта?',
        auth_forgot_password: 'Забыли пароль?',
        auth_back_to_login: 'Вернуться к входу',
        auth_login_id: 'Имя пользователя или Email',
        auth_login_id_placeholder: 'Введите имя пользователя или email',
        auth_password_placeholder: 'Введите пароль',
        auth_otp_sent: 'OTP код отправлен на email:',
        auth_otp_enter: 'Введите OTP код (6 цифр)',
        auth_btn_verify_email: 'Подтвердить Email',
        auth_resend_otp: 'Отправить OTP снова',
        auth_processing: 'Обработка...',
        auth_username_placeholder: 'например: myusername',
        auth_username_hint: '3-30 символов, строчные буквы, цифры и _',
        auth_email_placeholder: 'example@email.com',
        auth_password_min: 'Минимум 6 символов',
        auth_confirm_password_placeholder: 'Введите пароль снова',
        auth_btn_create_account: 'Создать аккаунт',
        auth_registering: 'Регистрация...',
        auth_otp_sent_register: 'OTP код отправлен на ваш email:',
        auth_otp_enter_6: 'Введите код подтверждения (6 цифр)',
        auth_btn_verify_account: 'Подтвердить аккаунт',
        auth_resend_code: 'Отправить код снова',
        auth_login_here: 'Войти здесь',
        auth_create_account: 'Создать новый аккаунт',
        
        // Account Page
        account_title: 'Управление аккаунтом',
        account_subtitle: 'Просмотр деталей и управление Premium подпиской',
        account_profile: 'Информация профиля',
        account_premium_status: 'Статус Premium',
        account_downloads: 'Загрузки',
        account_settings: 'Настройки',
        account_username: 'Имя пользователя',
        account_email: 'Email адрес',
        account_member_since: 'Участник с',
        account_account_type: 'Тип аккаунта',
        account_free: 'Бесплатный',
        account_premium: 'Premium',
        account_premium_active: 'Premium активен',
        account_premium_expires: 'Истекает',
        account_days_left: 'Осталось',
        account_days: 'дней',
        account_downloads_month: 'Загрузок в этом месяце',
        account_downloads_total: 'Всего загрузок',
        account_downloads_limit: 'Лимит',
        account_downloads_unlimited: 'Неограниченно',
        account_downloads_remaining: 'Осталось',
        account_premium_benefits: 'Преимущества Premium',
        account_benefit_unlimited: 'Неограниченные загрузки видео',
        account_benefit_no_ads: 'Без рекламы',
        account_benefit_priority: 'Максимальная скорость загрузки',
        account_benefit_support: 'Приоритетная поддержка',
        account_benefit_features: 'Ранний доступ к новым функциям',
        account_upgrade_premium: 'Обновить до Premium',
        account_renew_premium: 'Продлить Premium',
        account_payment_title: 'Оплата Premium',
        account_payment_subtitle: 'Поддержите любой суммой для получения 30 дней Premium',
        account_amount_popular: 'ПОПУЛЯРНО',
        account_amount_custom: 'Или введите свою сумму',
        account_amount_min: 'минимум',
        account_btn_pay: 'Оплатить сейчас',
        account_btn_home: 'Главная',
        account_btn_logout: 'Выйти',
        account_speed: 'Скорость загрузки',
        account_speed_max: 'Максимальная (Приоритет)',
        account_speed_standard: 'Стандартная',
        account_ads: 'Реклама',
        account_ads_off: 'Полностью отключена',
        account_ads_shown: 'Отображается',
        account_download_limit: 'Лимит загрузок',
        account_used: 'Использовано',
        account_times: 'раз',
        account_remaining: 'Осталось',
        account_no_downloads: 'Загрузки закончились',
        account_refresh_date: 'Обновится',
        account_next_month: 'В начале следующего месяца',
        premium_success_title: 'Большое спасибо!',
        premium_success_message: 'Транзакция успешна. Premium аккаунт активирован.',
        premium_success_support: 'Ваша поддержка помогает нам развивать Downloader Pro!',
        premium_success_btn: 'Начать использование',
        
        // Premium Page
        nav_premium: 'Premium',
        premium_page_title: 'Обновить до Premium',
        premium_page_subtitle: 'Используйте все функции без ограничений',
        premium_benefits_title: 'Преимущества Premium',
        premium_member_badge: '⭐ Premium участник',
        premium_free_badge: '🆓 Бесплатный участник',
        premium_expires: 'Истекает',
        premium_days_left: 'Осталось',
        premium_days: 'дней',
        premium_free_downloads_week: 'Бесплатные загрузки на этой неделе',
        premium_start_date: 'Дата начала',
        premium_amount: 'Сумма',
        premium_status: 'Статус',
        premium_active: '✓ Активен',
        premium_benefit_unlimited_desc: 'Неограниченные загрузки видео в месяц',
        premium_benefit_no_ads_desc: 'Плавный опыт, без прерываний',
        premium_benefit_priority_desc: 'Приоритетная обработка, быстрые загрузки',
        premium_benefit_support_desc: 'Быстрая поддержка при необходимости',
        premium_processing: 'Обработка...'
    }
};

// Get current language from localStorage or default to 'vi'
function getCurrentLanguage() {
    return localStorage.getItem('language') || 'vi';
}

// Set language
function setLanguage(lang) {
    localStorage.setItem('language', lang);
    applyTranslations(lang);
    updateLanguageUI(lang);
}

// Apply translations to page
function applyTranslations(lang) {
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (translations[lang] && translations[lang][key]) {
            // Check if it's an input placeholder
            if (element.tagName === 'INPUT' && element.hasAttribute('placeholder')) {
                element.placeholder = translations[lang][key];
            } else {
                element.textContent = translations[lang][key];
            }
        }
    });
    
    // Handle placeholder translations separately
    const placeholderElements = document.querySelectorAll('[data-i18n-placeholder]');
    placeholderElements.forEach(element => {
        const key = element.getAttribute('data-i18n-placeholder');
        if (translations[lang] && translations[lang][key]) {
            element.placeholder = translations[lang][key];
        }
    });
    
    // Update download complete messages
    updateDownloadCompleteMessages(lang);
}

// Update download complete messages
function updateDownloadCompleteMessages(lang) {
    const youtubeComplete = document.querySelector('#youtube-complete p');
    const tiktokComplete = document.querySelector('#tiktok-complete p');
    const youtubeSaveBtn = document.getElementById('youtube-save-btn');
    const tiktokSaveBtn = document.getElementById('tiktok-save-btn');
    
    if (youtubeComplete) youtubeComplete.textContent = translations[lang].download_complete;
    if (tiktokComplete) tiktokComplete.textContent = translations[lang].download_complete;
    if (youtubeSaveBtn) youtubeSaveBtn.textContent = translations[lang].btn_download_again;
    if (tiktokSaveBtn) tiktokSaveBtn.textContent = translations[lang].btn_download_again;
}

// Update language UI
function updateLanguageUI(lang) {
    const langFlags = {
        vi: '🇻🇳',
        en: '🇺🇸',
        ru: '🇷🇺'
    };
    
    const langIcon = document.querySelector('.lang-icon');
    const langText = document.querySelector('.lang-text');
    
    if (langIcon) langIcon.textContent = langFlags[lang] || '🇻🇳';
    if (langText) langText.textContent = translations[lang].lang_name;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    const currentLang = getCurrentLanguage();
    applyTranslations(currentLang);
    updateLanguageUI(currentLang);
    
    // Language switcher
    const langOptions = document.querySelectorAll('.lang-option');
    langOptions.forEach(option => {
        option.addEventListener('click', function() {
            const lang = this.getAttribute('data-lang');
            setLanguage(lang);
            
            // Close dropdown
            const dropdown = document.getElementById('lang-dropdown');
            if (dropdown) dropdown.classList.remove('active');
        });
    });
});
