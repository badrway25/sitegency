"""
Customizer views — live editor, iframe preview, AJAX save / upload.
"""
import secrets
import json
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.urls import reverse
from django.utils.translation import gettext as _

from catalog.models import TemplateItem
from .models import DemoSession, CustomizerMediaUpload
from .services import PreviewEngine


def _get_or_create_session(request, template):
    token = request.session.get('bw_token')
    if not token:
        token = secrets.token_urlsafe(24)
        request.session['bw_token'] = token
    session_obj, _ = DemoSession.objects.get_or_create(
        template=template,
        session_token=token,
        defaults={'data': {}, 'uploaded_media': {}},
    )
    return session_obj


@ensure_csrf_cookie
def customize(request, slug):
    template = get_object_or_404(TemplateItem, slug=slug, is_active=True)
    session_obj = _get_or_create_session(request, template)
    custom_fields = template.custom_fields.all().order_by('group', 'order')
    grouped = {}
    for f in custom_fields:
        grouped.setdefault(f.group, []).append(f)

    return render(request, 'customizer/customize.html', {
        'template': template,
        'session_obj': session_obj,
        'grouped_fields': grouped,
        'initial_data_json': json.dumps(session_obj.data or {}),
        'preview_url': reverse('customizer:customize_preview', kwargs={'slug': slug}),
        'save_label_json': json.dumps(_('Save Draft')),
        'saving_label_json': json.dumps(_('Saving…')),
        'saved_label_json': json.dumps(_('Saved')),
    })


def customize_preview(request, slug, page=None):
    template = get_object_or_404(TemplateItem, slug=slug, is_active=True)
    session_obj = _get_or_create_session(request, template)
    engine = PreviewEngine(
        template=template,
        page_slug=page,
        session_data=session_obj.data,
        is_customizer=True,
    )
    return engine.render()


@require_POST
def save_session(request, slug):
    template = get_object_or_404(TemplateItem, slug=slug, is_active=True)
    session_obj = _get_or_create_session(request, template)
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return HttpResponseBadRequest('invalid json')
    data = payload.get('data', {})
    if not isinstance(data, dict):
        return HttpResponseBadRequest('data must be object')
    session_obj.data.update(data)
    session_obj.save(update_fields=['data', 'updated_at'])
    return JsonResponse({'ok': True, 'session_id': str(session_obj.id)})


@require_POST
def upload_media(request, slug):
    template = get_object_or_404(TemplateItem, slug=slug, is_active=True)
    session_obj = _get_or_create_session(request, template)
    field_key = request.POST.get('field_key')
    file = request.FILES.get('file')
    if not field_key or not file:
        return HttpResponseBadRequest('missing field_key or file')
    upload = CustomizerMediaUpload.objects.create(
        session=session_obj, field_key=field_key, file=file,
        original_name=file.name,
    )
    url = upload.file.url
    session_obj.uploaded_media[field_key] = url
    session_obj.data[field_key] = url
    session_obj.save(update_fields=['uploaded_media', 'data', 'updated_at'])
    return JsonResponse({'ok': True, 'url': url, 'field_key': field_key})
