from asset_registry.models import PhysicalAsset, SoftwareAsset
from crispy_forms_gds.fields import DateInputField
from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Layout, Submit
from django import forms


class AssetSearchForm(forms.Form):
    search_terms = forms.CharField(label="")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios("search_terms"),
            Submit("submit", "Search"),
        )


class PhysicalAssetModelForm(forms.ModelForm):

    purchase_date = DateInputField()
    cost = forms.CharField()
    warranty_expire_date = DateInputField()
    date_assigned = DateInputField()
    date_returned = DateInputField()
    last_verified_date = DateInputField()

    class Meta:
        model = PhysicalAsset
        fields = [
            "asset_number",
            "finance_asset_number",
            "category",
            "status",
            "manufacturer",
            "model",
            "serial_number",
            "purchase_date",
            "cost",
            "warranty_expire_date",
            "location",
            "address",
            "date_assigned",
            "date_returned",
            "last_verified_date",
        ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.text("asset_number"),
            Field.text("finance_asset_number"),
            Field.select("category"),
            Field.select("status"),
            Field.text("manufacturer"),
            Field.text("model"),
            Field.text("serial_number"),
            Field("purchase_date"),
            Field.text("cost", field_width=5),
            Field("warranty_expire_date"),
            Field.text("location"),
            Field.text("address"),
            Field("date_assigned"),
            Field("date_returned"),
            Field("last_verified_date"),
        )


class PhysicalAssetCreateForm(PhysicalAssetModelForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.helper.layout.append(Submit("submit", "Create physical asset"))


class PhysicalAssetUpdateForm(PhysicalAssetModelForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.helper.layout.append(Submit("submit", "Update physical asset"))


class SoftwareAssetModelForm(forms.ModelForm):
    renewal_date = DateInputField()
    licences_available = forms.CharField()
    licences_issued = forms.CharField()

    class Meta:
        model = SoftwareAsset
        fields = [
            "software_name",
            "licence_number",
            "licence_password",
            "licences_available",
            "licences_issued",
            "renewal_date",
        ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.text("software_name"),
            Field.text("licence_number"),
            Field.text("licence_password"),
            Field.text("licences_available"),
            Field.text("licences_issued"),
            Field("renewal_date"),
        )


class SoftwareAssetCreateForm(SoftwareAssetModelForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.helper.layout.append(Submit("submit", "Create software asset"))


class SoftwareAssetUpdateForm(SoftwareAssetModelForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.helper.layout.append(Submit("submit", "Update software asset"))
