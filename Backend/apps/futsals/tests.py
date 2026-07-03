from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Court, Futsal, FutsalRole

User = get_user_model()


def make_user(email, phone):
    return User.objects.create_user(email=email, phone=phone, password="StrongPass123!")


def tiny_png(name="photo.png"):
    buf = BytesIO()
    Image.new("RGB", (2, 2), "green").save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


class FutsalRBACTests(APITestCase):
    def setUp(self):
        self.owner = make_user("owner@example.com", "9811111111")
        self.other = make_user("other@example.com", "9822222222")

    def test_create_futsal_makes_creator_owner(self):
        self.client.force_authenticate(self.owner)
        res = self.client.post(reverse("futsal-list"), {"name": "Kathmandu Futsal", "city": "KTM"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        futsal = Futsal.objects.get(slug=res.data["slug"])
        self.assertTrue(futsal.is_owner(self.owner))

    def test_non_staff_cannot_edit_futsal(self):
        self.client.force_authenticate(self.owner)
        slug = self.client.post(reverse("futsal-list"), {"name": "A", "city": "KTM"}).data["slug"]
        # other user tries to patch
        self.client.force_authenticate(self.other)
        res = self.client.patch(reverse("futsal-detail", args=[slug]), {"city": "Pokhara"})
        self.assertIn(res.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))

    def test_owner_can_add_manager_but_manager_cannot(self):
        self.client.force_authenticate(self.owner)
        slug = self.client.post(reverse("futsal-list"), {"name": "A", "city": "KTM"}).data["slug"]
        futsal = Futsal.objects.get(slug=slug)
        # owner adds manager
        res = self.client.post(reverse("futsalrole-list"),
                               {"user": str(self.other.pk), "futsal": str(futsal.pk),
                                "role": FutsalRole.Role.MANAGER})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # manager cannot grant roles
        self.client.force_authenticate(self.other)
        res = self.client.post(reverse("futsalrole-list"),
                               {"user": str(self.owner.pk), "futsal": str(futsal.pk),
                                "role": FutsalRole.Role.MANAGER})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_remove_last_owner(self):
        self.client.force_authenticate(self.owner)
        slug = self.client.post(reverse("futsal-list"), {"name": "A", "city": "KTM"}).data["slug"]
        futsal = Futsal.objects.get(slug=slug)
        role = futsal.roles.get(role=FutsalRole.Role.OWNER)
        res = self.client.delete(reverse("futsalrole-detail", args=[role.pk]))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_public_sees_only_active_futsals(self):
        f = Futsal.objects.create(name="Hidden", created_by=self.owner)  # PENDING by default
        res = self.client.get(reverse("futsal-list"))
        slugs = [x["slug"] for x in res.data["results"]]
        self.assertNotIn(f.slug, slugs)


class FutsalImageTests(APITestCase):
    def setUp(self):
        self.owner = make_user("owner@example.com", "9811111111")
        self.other = make_user("other@example.com", "9822222222")
        self.futsal = Futsal.objects.create(name="Pics FC", created_by=self.owner,
                                            status=Futsal.Status.ACTIVE)
        FutsalRole.objects.create(user=self.owner, futsal=self.futsal,
                                  role=FutsalRole.Role.OWNER)
        self.court = Court.objects.create(futsal=self.futsal, name="C")

    def test_owner_can_upload_futsal_image_and_it_nests(self):
        self.client.force_authenticate(self.owner)
        res = self.client.post(reverse("futsalimage-list"),
                               {"futsal": str(self.futsal.pk), "image": tiny_png(), "is_primary": True},
                               format="multipart")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        detail = self.client.get(reverse("futsal-detail", args=[self.futsal.slug]))
        self.assertEqual(len(detail.data["images"]), 1)

    def test_non_staff_cannot_upload(self):
        self.client.force_authenticate(self.other)
        res = self.client.post(reverse("futsalimage-list"),
                               {"futsal": str(self.futsal.pk), "image": tiny_png()},
                               format="multipart")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_court_supports_multiple_images(self):
        self.client.force_authenticate(self.owner)
        for i in range(2):
            res = self.client.post(reverse("courtimage-list"),
                                   {"court": str(self.court.pk), "image": tiny_png(f"c{i}.png")},
                                   format="multipart")
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        detail = self.client.get(reverse("court-detail", args=[self.court.pk]))
        self.assertEqual(len(detail.data["images"]), 2)
