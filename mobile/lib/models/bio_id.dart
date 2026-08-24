/// Mirrors backend/app/schemas/bioid.py BioIDResponse.
class BioId {
  const BioId({required this.id, required this.code, required this.status});

  final String id;
  final String code;
  final String status;

  factory BioId.fromJson(Map<String, dynamic> json) => BioId(
        id: json['id'] as String,
        code: json['code'] as String,
        status: json['status'] as String,
      );
}
