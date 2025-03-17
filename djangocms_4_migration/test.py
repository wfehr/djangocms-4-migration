def setup_v3_testproj():
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group, Permission

    from cms import api

    User = get_user_model()
    user, _ = User.objects.get_or_create(
        username="staff", is_staff=True, is_superuser=False
    )
    group, _ = Group.objects.get_or_create(name="Editors")
    group.user_set.add(user)

    user.user_permissions.add(Permission.objects.get(codename="add_title"))
    group.permissions.add(Permission.objects.get(codename="change_title"))

    page = api.create_page("Home", "base.html", "en")
    title = api.create_title("fr", "Home", page)
    placeholder = page.get_placeholders()[0]
    api.add_plugin(placeholder, "TextPlugin", "en", body="Hello World")
    api.add_plugin(placeholder, "TextPlugin", "fr", body="Bonjour le monde")
    page.publish("en")


def test_title_migration():
    """Minimal test if the title objects have been split and turned into page content
    objects with versions."""
    from cms.models import PageContent

    page_contents = PageContent.admin_manager.order_by("language").all()
    assert page_contents.count() == 2
    assert page_contents[0].language == "en"
    assert page_contents[1].language == "fr"
    assert page_contents[0].versions.first().state == "published"
    assert page_contents[1].versions.first().state == "draft"


def test_permissions_migration():
    """Check if the tiltle permissions have been migrated to page content permissions."""
    from django.contrib.auth import get_user_model

    User = get_user_model()

    user = User.objects.get(username="staff")

    assert user.has_perm("cms.add_pagecontent")
    assert user.has_perm("djangocms_versioning.add_pagecontentversion")
    assert user.has_perm("cms.change_pagecontent")
    assert user.has_perm("djangocms_versioning.change_pagecontentversion")

    user.groups.clear()  # Remove the user from the group -> lose change permission

    user = User.objects.get(username="staff")  # refetch from db
    assert not user.has_perm("cms.change_pagecontent")
    assert not user.has_perm("djangocms_versioning.change_pagecontentversion")


if __name__ == "__main__":
    import os
    import sys
    import traceback
    import types
    import django
    from cms import __version__

    if __version__.startswith("3"):
        os.environ["DJANGO_SETTINGS_MODULE"] = "cmsproject.settings"
        django.setup()
        setup_v3_testproj()
    else:
        os.environ["DJANGO_SETTINGS_MODULE"] = "cmsproject.settings4"
        django.setup()
        failed = False
        current_module = sys.modules[__name__]
        for name in dir(current_module):
            obj = getattr(current_module, name)
            if isinstance(obj, types.FunctionType) and name.startswith("test_"):
                try:
                    obj()
                    print("OK:", name)
                except AssertionError:
                    failed = True
                    print("FAIL:", name)
                    traceback.print_exc()
                except Exception as e:
                    failed = True
                    print("ERROR:", name, e)
                    traceback.print_exc()
        print("Done")
        if failed:
            sys.exit(1)
