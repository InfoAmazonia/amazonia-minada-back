// Run with mongosh as an administrator. Passwords come only from a private JSON file.
const fs = require('fs');
const policy = JSON.parse(fs.readFileSync(process.env.MINADA_APP_POLICY_FILE || '/tmp/minada-app-roles.json', 'utf8'));
const passwords = JSON.parse(fs.readFileSync(process.env.MINADA_APP_PASSWORD_FILE || '/tmp/minada-app-passwords.json', 'utf8'));
if (policy.database !== 'icfj') throw new Error('Unexpected application database');
const target = db.getSiblingDB(policy.database);
for (const spec of policy.roles) {
    if (target.getRole(spec.role)) throw new Error(`Role already exists: ${spec.role}; inspect before changing it`);
}
for (const spec of policy.users) {
    if (target.getUser(spec.user)) throw new Error(`User already exists: ${spec.user}; inspect before changing it`);
    if (typeof passwords[spec.user] !== 'string' || passwords[spec.user].length < 32) {
        throw new Error(`Missing or weak password for ${spec.user}`);
    }
}
for (const spec of policy.roles) target.createRole(spec);
for (const spec of policy.users) target.createUser({ ...spec, pwd: passwords[spec.user] });
print(JSON.stringify({ database: policy.database, users: policy.users.map(spec => ({ user: spec.user, roles: spec.roles })) }));
