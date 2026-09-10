# COMMS Schema ERD

```mermaid
erDiagram
    comms__comms.announcements {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string title
        text content
        boolean is_active
        datetime starts_at
        datetime ends_at
        datetime created_at
        datetime updated_at
    }
    comms__comms.campaign_recipients {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer campaign_id [FK]
        integer user_id
        string email
        string status_code
        datetime sent_at
        datetime delivered_at
        datetime opened_at
        datetime clicked_at
        datetime bounced_at
        datetime created_at
    }
    comms__comms.campaign_recipients ||--o| comms__email_campaigns : has
    comms__comms.chat_attachments {
        guid uuid [UK]
        integer version
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer message_id
        string message_type
        string attachment_type
        string file_url
        string file_name
        integer file_size_bytes
        string mime_type
        string thumbnail_url
        integer duration_seconds
        text waveform_json
        boolean is_processed
    }
    comms__comms.chat_read_receipts {
        guid uuid [UK]
        integer version
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer message_id
        string message_type
        integer employee_id
        datetime read_at
    }
    comms__comms.communication_audit_trails {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string entity_type
        integer entity_id
        integer user_id
        string action
        string channel
        text content_preview
        json metadata_json
        datetime created_at
    }
    comms__comms.direct_chat_messages {
        integer id [PK]
        integer room_id [FK]
        integer sender_id [FK]
        text message
        string message_type
        datetime read_at
        boolean is_deleted
        datetime created_at
    }
    comms__comms.direct_chat_messages ||--o| comms__direct_chat_rooms : has
    comms__comms.direct_chat_messages ||--o| accounts__users : has
    comms__comms.direct_chat_rooms {
        integer id [PK]
        string chat_id [UK]
        integer participant_one_id [FK]
        integer participant_two_id [FK]
        string country_code [FK]
        boolean is_masked
        boolean is_active
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    comms__comms.direct_chat_rooms ||--o| accounts__users : has
    comms__comms.direct_chat_rooms ||--o| accounts__users : has
    comms__comms.direct_chat_rooms ||--o| country__country_configs : has
    comms__comms.email_campaign_logs {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer campaign_id [FK]
        string recipient_email
        string status_code
        datetime sent_at
        datetime delivered_at
        datetime opened_at
        datetime created_at
    }
    comms__comms.email_campaign_logs ||--o| comms__email_campaigns : has
    comms__comms.email_campaigns {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer updated_by
        integer id [PK]
        string name
        string subject
        string status_code
        datetime send_at
        integer created_by
        datetime created_at
        datetime updated_at
        string from_name
        text target_audience
        datetime scheduled_at
        datetime sent_at
        integer sent_count
        integer open_count
        integer click_count
        string country_code
    }
    comms__comms.email_delivery_events {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string event_type
        string recipient_email
        string subject
        string status_code
        json details
        datetime created_at
    }
    comms__comms.email_folders {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer employee_id
        string name
        string folder_type
        integer sort_order
        boolean is_system
        datetime created_at
    }
    comms__comms.email_runtime_configs {
        guid uuid [UK]
        integer version
        datetime created_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string provider
        string resend_api_key
        string resend_webhook_secret
        string smtp_host
        integer smtp_port
        string smtp_username
        string smtp_password
        boolean is_smtp_use_tls
        boolean is_smtp_use_ssl
        integer smtp_timeout_seconds
        string email_from_default
        string email_from_promotional
        string email_from_transactional
        string email_from_notification
        string email_from_alert
        string email_from_verification
        string email_from_login_verification
        string email_from_password_reset
        datetime updated_at
    }
    comms__comms.email_suppressions {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string email
        string reason
        string source
        string provider
        string status_code
        text notes
        datetime suppressed_at
        datetime last_event_at
        datetime created_at
    }
    comms__comms.email_templates {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer updated_by
        integer id [PK]
        string name [UK]
        string subject
        text content
        string template_type
        boolean is_active
        integer created_by
        datetime created_at
        datetime updated_at
    }
    comms__comms.employee_communication_threads {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer entity_id
        string entity_type
        text participants
        datetime created_at
        string country_code
    }
    comms__comms.entity_chat_messages {
        integer id [PK]
        integer thread_id [FK]
        integer sender_id [FK]
        text message
        string message_type
        datetime read_at
        boolean is_deleted
        datetime created_at
    }
    comms__comms.entity_chat_messages ||--o| comms__entity_chat_threads : has
    comms__comms.entity_chat_messages ||--o| accounts__users : has
    comms__comms.entity_chat_threads {
        integer id [PK]
        string entity_type
        integer entity_id
        string title
        boolean is_active
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    comms__comms.escalation_sla_logs {
        integer id [PK]
        integer message_id
        string message_type
        integer original_recipient_id [FK]
        integer escalated_to_user_id [FK]
        string escalated_to_role
        string priority
        integer elapsed_minutes
        string status
        datetime escalated_at
        datetime acknowledged_at
        boolean is_deleted
        datetime created_at
    }
    comms__comms.escalation_sla_logs ||--o| accounts__users : has
    comms__comms.escalation_sla_logs ||--o| accounts__users : has
    comms__comms.escalation_sla_rules {
        integer id [PK]
        string country_code [FK]
        string priority
        integer escalate_after_minutes
        string escalate_to_role
        string notify_via
        boolean is_active
        datetime created_at
    }
    comms__comms.escalation_sla_rules ||--o| country__country_configs : has
    comms__comms.external_contact_maskings {
        guid uuid [UK]
        integer version
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer user_id
        string external_contact_type
        integer external_contact_id
        string masked_phone
        string masked_email
    }
    comms__comms.faqs {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        text question
        text answer
        string category
        datetime created_at
        string country_code
    }
    comms__comms.flash_sale_items {
        guid uuid [UK]
        integer version
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer flash_sale_id [FK]
        integer product_id [FK]
        numeric original_price
        numeric discounted_price
        string country_code
        integer quantity_limit
    }
    comms__comms.flash_sale_items ||--o| promotions__flash_sales : has
    comms__comms.flash_sale_items ||--o| catalog__products : has
    comms__comms.group_chat_members {
        integer id [PK]
        integer room_id [FK]
        integer user_id [FK]
        string role
        datetime joined_at
        boolean is_deleted
    }
    comms__comms.group_chat_members ||--o| comms__group_chat_rooms : has
    comms__comms.group_chat_members ||--o| accounts__users : has
    comms__comms.group_chat_messages {
        integer id [PK]
        integer room_id [FK]
        integer sender_id [FK]
        text message
        string message_type
        datetime read_at
        boolean is_deleted
        datetime created_at
    }
    comms__comms.group_chat_messages ||--o| comms__group_chat_rooms : has
    comms__comms.group_chat_messages ||--o| accounts__users : has
    comms__comms.group_chat_rooms {
        integer id [PK]
        string chat_id [UK]
        string name
        string country_code [FK]
        boolean is_encrypted
        boolean is_active
        integer created_by_id [FK]
        datetime created_at
        datetime updated_at
        boolean is_deleted
    }
    comms__comms.group_chat_rooms ||--o| country__country_configs : has
    comms__comms.group_chat_rooms ||--o| accounts__users : has
    comms__comms.help_categories {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string name
        text description
        datetime created_at
    }
    comms__comms.incident_action_items {
        integer id [PK]
        integer war_room_id [FK]
        integer assignee_id [FK]
        string title
        text description
        string status
        string priority
        datetime due_date
        datetime created_at
        datetime completed_at
        datetime updated_at
        boolean is_deleted
    }
    comms__comms.incident_action_items ||--o| comms__incident_war_rooms : has
    comms__comms.incident_action_items ||--o| accounts__users : has
    comms__comms.incident_threads {
        integer id [PK]
        integer war_room_id [FK]
        integer participant_id [FK]
        text message
        datetime created_at
        datetime updated_at
        boolean is_deleted
    }
    comms__comms.incident_threads ||--o| comms__incident_war_rooms : has
    comms__comms.incident_threads ||--o| accounts__users : has
    comms__comms.incident_war_rooms {
        integer id [PK]
        string incident_id [UK]
        string title
        string severity
        string status
        integer created_by_id [FK]
        datetime started_at
        datetime resolved_at
        datetime closed_at
        json context_data
        boolean is_deleted
        datetime updated_at
    }
    comms__comms.incident_war_rooms ||--o| accounts__users : has
    comms__comms.internal_channel_members {
        guid uuid [UK]
        integer version
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer channel_id [FK]
        integer user_id
        string role
        datetime joined_at
    }
    comms__comms.internal_channel_members ||--o| comms__internal_channels : has
    comms__comms.internal_channels {
        guid uuid [UK]
        integer version
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer updated_by
        integer id [PK]
        string entity_type
        integer entity_id
        string name
        string channel_id [UK]
        text description
        boolean is_public
        integer created_by
        string country_code
        json allowed_roles
    }
    comms__comms.internal_emails {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer sender_id
        string subject
        text body_html
        text body_text
        text recipients
        string thread_id
        boolean is_external
        string external_message_id
        integer in_reply_to_id [FK]
        integer folder_id [FK]
        datetime created_at
        datetime updated_at
        string country_code
    }
    comms__comms.internal_emails ||--o| comms__internal_emails : has
    comms__comms.internal_emails ||--o| comms__email_folders : has
    comms__comms.internal_messages {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer channel_id [FK]
        integer user_id
        text message
        string message_type
        boolean is_masked
        datetime read_at
        datetime created_at
    }
    comms__comms.internal_messages ||--o| comms__internal_channels : has
    comms__comms.internal_notices {
        integer id [PK]
        string title
        text content
        string priority
        boolean is_active
        datetime valid_from
        datetime valid_to
        datetime created_at
    }
    comms__comms.masked_messages {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer sender_id
        string recipient_ref
        integer message_hash
        text content
        datetime created_at
        string country_code
    }
    comms__comms.meeting_recordings {
        integer id [PK]
        boolean is_deleted
        string room_id
        integer started_by_id [FK]
        string recording_url
        integer duration_seconds
        string status_code
        datetime started_at
        datetime ended_at
        datetime created_at
        datetime updated_at
    }
    comms__comms.meeting_recordings ||--o| accounts__users : has
    comms__comms.messages {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code [FK]
        integer from_user_id
        integer to_user_id
        string subject
        text body
        string entity_type
        integer entity_id
        string priority
        string category
        string status
        datetime read_at
        datetime created_at
    }
    comms__comms.messages ||--o| country__country_configs : has
    comms__comms.news_articles {
        integer id [PK]
        boolean is_deleted
        integer source_id [FK]
        string external_id
        string content_hash
        string title
        text summary
        text content
        string url
        string image_url
        datetime published_at
        string country_code
        string ai_sentiment
        json ai_tags
        boolean is_published
        datetime created_at
        datetime updated_at
    }
    comms__comms.news_articles ||--o| comms__news_sources : has
    comms__comms.news_sources {
        integer id [PK]
        string name
        string url
        string source_type
        boolean api_key_required
        string category
        boolean is_active
        datetime created_at
    }
    comms__comms.newsletter_subscribers {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string email [UK]
        datetime created_at
        datetime updated_at
    }
    comms__comms.notifications {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer user_id
        string type
        string title
        text message
        string channel
        string priority
        boolean is_read
        datetime read_at
        string link
        string template
        json variables
        datetime scheduled_at
        string status_code
        datetime created_at
        string country_code
    }
    comms__comms.proxy_call_logs {
        guid uuid [UK]
        integer version
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer channel_id [FK]
        integer caller_id
        integer callee_id
        string direction
        integer duration_seconds
        string call_recording_url
        boolean is_recorded
        datetime started_at
        datetime ended_at
    }
    comms__comms.proxy_call_logs ||--o| comms__proxy_channels : has
    comms__comms.proxy_channels {
        guid uuid [UK]
        integer version
        datetime created_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string entity_type
        integer entity_id
        string proxy_phone [UK]
        string proxy_email [UK]
        json participants
        datetime updated_at
    }
    comms__comms.proxy_messages {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer session_id [FK]
        integer sender_id
        integer recipient_id
        string message_type
        text content
        boolean is_masked
        datetime read_at
        datetime created_at
    }
    comms__comms.proxy_messages ||--o| comms__proxy_sessions : has
    comms__comms.proxy_sessions {
        guid uuid [UK]
        integer version
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer channel_id [FK]
        integer participant_one_id
        integer participant_two_id
        datetime started_at
        datetime ended_at
        boolean is_encrypted
        json session_metadata
    }
    comms__comms.proxy_sessions ||--o| comms__proxy_channels : has
    comms__comms.support_ticket_replies {
        integer id [PK]
        integer ticket_id [FK]
        integer sender_id [FK]
        text message
        datetime created_at
        string country_code
    }
    comms__comms.support_ticket_replies ||--o| comms__support_tickets : has
    comms__comms.support_ticket_replies ||--o| accounts__users : has
    comms__comms.support_tickets {
        integer id [PK]
        boolean is_deleted
        integer user_id [FK]
        string subject
        string priority
        string status
        datetime created_at
        datetime updated_at
        string country_code
    }
    comms__comms.support_tickets ||--o| accounts__users : has
    comms__comms.ticket_attachments {
        integer id [PK]
        integer ticket_reply_id [FK]
        integer ticket_id [FK]
        string file_url
        datetime created_at
        string country_code
    }
    comms__comms.ticket_attachments ||--o| comms__support_ticket_replies : has
    comms__comms.ticket_attachments ||--o| comms__support_tickets : has
    comms__comms.ticket_messages {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer ticket_id [FK]
        integer sender_id
        text message
        boolean is_admin
        datetime created_at
        string country_code
    }
    comms__comms.ticket_messages ||--o| comms__support_tickets : has
    comms__comms.video_room_participants {
        integer id [PK]
        integer room_id [FK]
        integer user_id [FK]
        string role
        datetime joined_at
        datetime left_at
        boolean is_deleted
    }
    comms__comms.video_room_participants ||--o| comms__video_rooms : has
    comms__comms.video_room_participants ||--o| accounts__users : has
    comms__comms.video_room_recordings {
        integer id [PK]
        integer room_id [FK]
        integer started_by_id [FK]
        string recording_url
        integer duration_seconds
        string status
        datetime started_at
        datetime ended_at
        boolean is_deleted
    }
    comms__comms.video_room_recordings ||--o| comms__video_rooms : has
    comms__comms.video_room_recordings ||--o| accounts__users : has
    comms__comms.video_rooms {
        integer id [PK]
        string room_id [UK]
        string room_uuid [UK]
        string name
        string country_code [FK]
        integer created_by_id [FK]
        boolean is_boardroom
        string status
        integer max_participants
        boolean recording_enabled
        boolean watermark_enabled
        boolean transcription_enabled
        datetime started_at
        datetime ended_at
        datetime created_at
        datetime updated_at
        boolean is_deleted
    }
    comms__comms.video_rooms ||--o| country__country_configs : has
    comms__comms.video_rooms ||--o| accounts__users : has
    comms__comms.war_room_templates {
        integer id [PK]
        string name
        string severity
        boolean auto_assign
        json template_data
        boolean is_deleted
        datetime created_at
    }
```