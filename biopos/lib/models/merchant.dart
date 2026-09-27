/// Mirrors backend/app/schemas/merchants.py MerchantResponse.
class Merchant {
  const Merchant({
    required this.id,
    required this.businessName,
    required this.merchantCode,
    required this.status,
  });

  final String id;
  final String businessName;
  final String merchantCode;
  final String status;

  factory Merchant.fromJson(Map<String, dynamic> json) => Merchant(
        id: json['id'] as String,
        businessName: json['business_name'] as String,
        merchantCode: json['merchant_code'] as String,
        status: json['status'] as String,
      );
}
