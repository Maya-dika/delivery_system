from .models import RoutingRule
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist

def get_expected_route(from_wh, to_wh):
    try:
        rule = RoutingRule.objects.filter(from_warehouse=from_wh, to_warehouse=to_wh).first()
        if rule:
            return rule.get_full_route()
        else:
            if from_wh == to_wh:
                return [from_wh]
            else:
                return [from_wh, to_wh]
    except Exception:
        return []


def render_not_found(request, message="The requested item was not found."):
    """
    Renders a custom not found page for restricted object access.
    """
    return render(request, "layouts/page_404.html", {
        "message": message
    }, status=404)


def get_object_references(instance, *, include_counts: bool = False):
    """Inspect reverse relations to find where an object is referenced.

    Works for FK/OneToOne/M2M without hardcoding model names. Returns a list of
    dicts: { 'model': ModelClass, 'field': str|None, 'type': str, 'count': int|None }.
    """
    refs = []
    for rel in instance._meta.related_objects:
        accessor = rel.get_accessor_name()
        try:
            if rel.one_to_one:
                try:
                    obj = getattr(instance, accessor)
                    if obj is not None:
                        refs.append({
                            'model': rel.related_model,
                            'field': getattr(rel, 'field', None) and rel.field.name,
                            'type': 'one_to_one',
                            'count': 1 if include_counts else None,
                        })
                except ObjectDoesNotExist:
                    pass
            elif rel.one_to_many:
                manager = getattr(instance, accessor)
                if manager.exists():
                    refs.append({
                        'model': rel.related_model,
                        'field': rel.field.name,
                        'type': 'one_to_many',
                        'count': (manager.count() if include_counts else None),
                    })
            elif rel.many_to_many:
                manager = getattr(instance, accessor)
                if manager.exists():
                    refs.append({
                        'model': rel.related_model,
                        'field': getattr(rel, 'field', None) and rel.field.name,
                        'type': 'many_to_many',
                        'count': (manager.count() if include_counts else None),
                    })
        except Exception:
            # Be safe and skip relations we can't resolve
            continue
    return refs