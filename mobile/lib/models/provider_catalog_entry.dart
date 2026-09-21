/// Mirrors backend/app/schemas/provider_catalog.py ProviderCatalogEntryResponse.
/// The source of truth for which financial providers exist and can be
/// connected — see docs/architecture.md "Provider catalog". Replaces a
/// hardcoded provider list in the UI so a new market/partner shows up here
/// without a client release.
class ProviderCatalogEntry {
  const ProviderCatalogEntry({
    required this.code,
    required this.displayName,
    required this.countryCode,
    required this.currency,
    required this.category,
    required this.status,
  });

  final String code;
  final String displayName;
  final String countryCode;
  final String currency;
  final String category;
  final String status;

  bool get isAvailable => status == 'AVAILABLE';

  factory ProviderCatalogEntry.fromJson(Map<String, dynamic> json) => ProviderCatalogEntry(
        code: json['code'] as String,
        displayName: json['display_name'] as String,
        countryCode: json['country_code'] as String,
        currency: json['currency'] as String,
        category: json['category'] as String,
        status: json['status'] as String,
      );
}
