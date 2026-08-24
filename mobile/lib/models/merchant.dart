/// Mirrors backend/app/schemas/merchants.py MerchantResponse.
class Merchant {
  const Merchant({required this.id, required this.businessName, required this.merchantCode});

  final String id;
  final String businessName;
  final String merchantCode;

  factory Merchant.fromJson(Map<String, dynamic> json) => Merchant(
        id: json['id'] as String,
        businessName: json['business_name'] as String,
        merchantCode: json['merchant_code'] as String,
      );
}
